"""Foydalanuvchi shablonlarini (postprotsessorlar) xavfsiz chiqarish.

Jinja2 sandbox kodni himoya qiladi (fayl, import, ichki atributlar yopiq), lekin resursni emas:
'x'.center(10**9), ulkan sikllar yoki formatlash asosiy serverni to'xtatib qo'yishi mumkin. Shuning uchun
shablon alohida yordamchi jarayonda bajariladi: xotira chegarasi (Linux), vaqt chegarasi (oshsa jarayon
o'ldiriladi va qayta ochiladi), chiqish hajmi chegarasi. Bu modul ilovaning boshqa qismlarini import
qilmaydi — yordamchi jarayon yengil bo'lsin.

Sozlash: MEBELIX_TEMPLATE_TIMEOUT (s, standart 20), MEBELIX_TEMPLATE_INPROC=1 — jarayonsiz (faqat test/debug).
"""
from __future__ import annotations

import atexit
import multiprocessing as mp
import os
import threading
import time

from jinja2.sandbox import SandboxedEnvironment, SecurityError

MAX_OUTPUT = 20_000_000              # bitta fayl matni, belgi
MAX_LOOP = 1_000_000                 # range() larning jami elementlari
MAX_MEMORY = 1024 * 1024 * 1024      # yordamchi jarayon xotirasi (Linux, RLIMIT_AS)


def timeout_s() -> float:
    try:
        return max(1.0, float(os.getenv("MEBELIX_TEMPLATE_TIMEOUT", "20")))
    except ValueError:
        return 20.0


class TemplateLimit(Exception):
    """Shablon chegaradan chiqdi (hajm / vaqt / sikl / xotira)."""


class TemplateFailed(Exception):
    """Shablon xatosi (sintaksis, sandbox taqiqi, hisoblash xatosi) — matni foydalanuvchiga."""


def fnum(v, n: int = 1) -> str:
    """Shablondagi f(v, n): sonni n xona bilan, nuqta orqali (1500.0 → «1500», 12.345 → «12.3»)."""
    try:
        n = max(0, min(10, int(n)))
        r = round(float(v), n)
    except (TypeError, ValueError, OverflowError):
        return str(v)
    if r != r or r in (float("inf"), float("-inf")):
        return str(r)
    return str(int(r)) if r == int(r) else f"{r:.{n}f}"


class _Sandbox(SandboxedEnvironment):
    """Jinja2 sandbox + ulkan ko'paytirish/darajani taqiqlash ('x' * 10**9, 9 ** 99999)."""
    intercepted_binops = frozenset(["*", "**"])

    def call_binop(self, context, operator, left, right):
        if operator == "**" and isinstance(right, (int, float)) and abs(right) > 64:
            raise SecurityError("** > 64")
        if operator == "*":
            for a, b in ((left, right), (right, left)):
                if isinstance(a, (str, bytes, list, tuple)) and isinstance(b, int) and len(a) * b > MAX_OUTPUT:
                    raise SecurityError("result too large")
        return super().call_binop(context, operator, left, right)


def _env() -> _Sandbox:
    env = _Sandbox(autoescape=False, trim_blocks=False, lstrip_blocks=False)
    used = [0]

    def budget_range(*args):
        r = range(*args)
        used[0] += len(r)
        if len(r) > 100_000 or used[0] > MAX_LOOP:
            raise TemplateLimit(f"range(): > {MAX_LOOP}")
        return r
    env.globals["range"] = budget_range
    return env


def render_inproc(src: str, ctx: dict, max_output: int = MAX_OUTPUT, max_seconds: float | None = None) -> str:
    """Shablonni joriy jarayonda chiqarish (hajm, vaqt — faqat chiqish bo'laklari orasida — va sikl chegarasi)."""
    max_seconds = max_seconds or timeout_s()
    tpl = _env().from_string(src)
    out: list[str] = []
    size, t0 = 0, time.monotonic()
    for chunk in tpl.generate(**{"f": fnum, **ctx}):
        size += len(chunk)
        if size > max_output:
            raise TemplateLimit(f"> {max_output} belgi / символов")
        if time.monotonic() - t0 > max_seconds:
            raise TemplateLimit(f"> {max_seconds:.0f} s")
        out.append(chunk)
    return "".join(out)


# ───────────────────────── yordamchi jarayon ─────────────────────────
def _worker_init() -> None:
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (MAX_MEMORY, MAX_MEMORY))
    except Exception:  # noqa: BLE001 — Windows / chegara qo'yib bo'lmadi: vaqt chegarasi baribir ishlaydi
        pass


def _job(src: str, ctx: dict, max_output: int) -> tuple[str, str]:
    try:
        return "ok", render_inproc(src, ctx, max_output)
    except MemoryError:
        return "limit", "MemoryError"
    except TemplateLimit as e:
        return "limit", str(e)
    except Exception as e:  # noqa: BLE001 — har qanday shablon xatosi matn sifatida qaytadi
        return "err", f"{type(e).__name__}: {e}"


_pool = None
_pool_lock = threading.Lock()


def _get_pool():
    global _pool
    with _pool_lock:
        if _pool is None:
            _pool = mp.get_context("spawn").Pool(3, initializer=_worker_init, maxtasksperchild=200)
        return _pool


def _kill_pool(pool) -> None:
    global _pool
    with _pool_lock:
        if _pool is pool:
            _pool = None
    try:
        pool.terminate()
    except Exception:  # noqa: BLE001
        pass


@atexit.register
def _shutdown() -> None:
    if _pool is not None:
        _kill_pool(_pool)


def render(src: str, ctx: dict, max_output: int = MAX_OUTPUT) -> str:
    """Shablonni chiqarish: yordamchi jarayonda, chegaralar bilan. Xato — TemplateFailed / TemplateLimit."""
    if os.getenv("MEBELIX_TEMPLATE_INPROC") == "1":
        try:
            return render_inproc(src, ctx, max_output)
        except TemplateLimit:
            raise
        except Exception as e:  # noqa: BLE001
            raise TemplateFailed(f"{type(e).__name__}: {e}") from e
    ctx = {k: v for k, v in ctx.items() if k != "f"}      # f — yordamchi jarayonda qo'shiladi
    pool = _get_pool()
    job = pool.apply_async(_job, (src, ctx, max_output))
    t = timeout_s()
    try:
        # shablon o'zi ham chiqish bo'laklari orasida t ni tekshiradi; tashqi kutish navbatni ham qamraydi
        kind, val = job.get(t * 2)
    except mp.TimeoutError:
        _kill_pool(pool)                 # cheksiz sikl — jarayon o'ldiriladi, keyingi so'rovda yangisi ochiladi
        raise TemplateLimit(f"> {t:.0f} s") from None
    if kind == "ok":
        return val
    if kind == "limit":
        raise TemplateLimit(val)
    raise TemplateFailed(val)
