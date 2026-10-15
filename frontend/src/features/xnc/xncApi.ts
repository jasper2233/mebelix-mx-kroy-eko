// XNC shablonlar kutubxonasi va ishlov markazi postprotsessori uchun API hooklari.
import { useQuery } from "@tanstack/react-query";
import { get } from "../../api/client";
import type { XncPostprocessor, XncTemplate, XncTemplateInfo } from "../../api/types";

export const useXncTemplates = (lang: string, enabled = true) =>
  useQuery({ queryKey: ["xnc-templates", lang], enabled, queryFn: () => get<XncTemplateInfo[]>("/xnc/templates", { lang }) });

export const useXncTemplate = (id: string | null, lang: string) =>
  useQuery({ queryKey: ["xnc-template", id, lang], enabled: !!id, queryFn: () => get<XncTemplate>(`/xnc/templates/${id}`, { lang }) });

export const useXncPostprocessors = (enabled = true) =>
  useQuery({ queryKey: ["xnc-postprocessors"], enabled, queryFn: () => get<XncPostprocessor[]>("/xnc/postprocessors") });
