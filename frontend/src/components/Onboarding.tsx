"use client";

import { useState, useEffect, useCallback } from "react";
import { t, getLang, onLangChange, setLang, type LangCode } from "@/lib/i18n";

export default function Onboarding({ onComplete }: { onComplete: () => void }) {
  const [step, setStep] = useState(0);
  const [visible, setVisible] = useState(true);
  const [animating, setAnimating] = useState(false);
  const [lang, setLangState] = useState<LangCode>(getLang());

  useEffect(() => {
    return onLangChange((l) => setLangState(l));
  }, []);

  const STEPS = [
    {
      title: t("onboarding.step1.title"),
      description: t("onboarding.step1.desc"),
      icon: t("onboarding.step1.icon"),
    },
    {
      title: t("onboarding.step2.title"),
      description: t("onboarding.step2.desc"),
      icon: t("onboarding.step2.icon"),
      highlight: "graph-selector",
    },
    {
      title: t("onboarding.step3.title"),
      description: t("onboarding.step3.desc"),
      icon: t("onboarding.step3.icon"),
      highlight: "node-list",
    },
    {
      title: t("onboarding.step4.title"),
      description: t("onboarding.step4.desc"),
      icon: t("onboarding.step4.icon"),
      highlight: "score-panel",
    },
    {
      title: t("onboarding.step5.title"),
      description: t("onboarding.step5.desc"),
      icon: t("onboarding.step5.icon"),
      highlight: "view-toggle",
    },
    {
      title: t("onboarding.step6.title"),
      description: t("onboarding.step6.desc"),
      icon: t("onboarding.step6.icon"),
    },
    {
      title: t("onboarding.step7.title"),
      description: t("onboarding.step7.desc"),
      icon: t("onboarding.step7.icon"),
    },
    {
      title: t("onboarding.step8.title"),
      description: t("onboarding.step8.desc"),
      icon: t("onboarding.step8.icon"),
    },
  ];

  const current = STEPS[step];
  const isLast = step === STEPS.length - 1;
  const isFirst = step === 0;

  const goNext = useCallback(() => {
    if (isLast) {
      setAnimating(true);
      setTimeout(() => {
        setVisible(false);
        onComplete();
      }, 300);
      return;
    }
    setAnimating(true);
    setTimeout(() => {
      setStep((s) => s + 1);
      setAnimating(false);
    }, 200);
  }, [isLast, onComplete]);

  const goPrev = useCallback(() => {
    if (isFirst) return;
    setAnimating(true);
    setTimeout(() => {
      setStep((s) => s - 1);
      setAnimating(false);
    }, 200);
  }, [isFirst]);

  const skip = useCallback(() => {
    setAnimating(true);
    setTimeout(() => {
      setVisible(false);
      onComplete();
    }, 200);
  }, [onComplete]);

  // Keyboard navigation
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === "Enter") goNext();
      if (e.key === "ArrowLeft") goPrev();
      if (e.key === "Escape") skip();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [goNext, goPrev, skip]);

  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-surface-overlay animate-fade-in">
      <div
        className={`bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden transition-all duration-300 ${
          animating ? "opacity-0 scale-95" : "opacity-100 scale-100"
        }`}
      >
        {/* Language switcher + Progress bar */}
        <div className="flex items-center gap-2 px-6 pt-6 pb-2">
          <div className="flex gap-1 flex-1">
            {STEPS.map((_, i) => (
              <div
                key={i}
                className={`flex-1 h-1 rounded-full transition-colors duration-300 ${
                  i <= step ? "bg-primary-500" : "bg-slate-200"
                }`}
              />
            ))}
          </div>
          <button
            onClick={() => setLang(lang === "zh-CN" ? "en-US" : "zh-CN")}
            className="text-[10px] px-2 py-0.5 rounded-md border border-slate-200 text-slate-500 hover:text-primary-600 hover:border-primary-300 transition-colors"
            title="Switch language / 切换语言"
          >
            {lang === "zh-CN" ? "EN" : "中文"}
          </button>
        </div>

        {/* Content */}
        <div className="p-6 pt-4">
          <div className="text-3xl mb-3">{current.icon}</div>
          <h2 className="text-lg font-bold text-slate-800 mb-2">
            {current.title}
          </h2>
          <p className="text-sm text-slate-500 leading-relaxed">
            {current.description}
          </p>
        </div>

        {/* Actions */}
        <div className="px-6 pb-6 flex items-center justify-between">
          <button
            onClick={skip}
            className="text-xs text-slate-400 hover:text-slate-600 transition-colors"
          >
            {t("onboarding.skip")}
          </button>
          <div className="flex gap-2">
            {!isFirst && (
              <button
                onClick={goPrev}
                className="btn-ghost text-xs px-3 py-1.5 rounded-lg"
              >
                {t("onboarding.back")}
              </button>
            )}
            <button
              onClick={goNext}
              className="btn-primary text-xs px-4 py-2 rounded-lg font-medium"
            >
              {isLast ? t("onboarding.start") : t("onboarding.next")}
            </button>
          </div>
        </div>

        {/* Step counter */}
        <div className="text-center pb-4">
          <span className="text-[10px] text-slate-300">
            {step + 1} / {STEPS.length}
          </span>
        </div>
      </div>
    </div>
  );
}
