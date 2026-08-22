const progressBar = document.querySelector(".reading-progress-bar");

if (progressBar) {
  const updateReadingProgress = () => {
    const scrollable =
      document.documentElement.scrollHeight - window.innerHeight;
    const progress = scrollable > 0 ? window.scrollY / scrollable : 0;
    progressBar.style.width = `${Math.min(Math.max(progress, 0), 1) * 100}%`;
  };

  updateReadingProgress();
  window.addEventListener("scroll", updateReadingProgress, { passive: true });
  window.addEventListener("resize", updateReadingProgress);
}

const COPY_ICON = `
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M9 8h10a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1Z"></path>
    <path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3"></path>
  </svg>`;
const SUCCESS_ICON = `
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="m5 12 4 4L19 6"></path>
  </svg>`;
const ERROR_ICON = `
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="m6 6 12 12M18 6 6 18"></path>
  </svg>`;
const COPY_RESET_DELAY = 2000;

const getCodeLanguage = (code) => {
  const languageClass = [...code.classList].find((className) =>
    className.startsWith("language-"),
  );

  return languageClass?.slice("language-".length) || "text";
};

const setCopyButtonState = (button, state) => {
  const states = {
    idle: { icon: COPY_ICON, label: "复制代码" },
    success: { icon: SUCCESS_ICON, label: "已复制" },
    error: { icon: ERROR_ICON, label: "复制失败" },
  };
  const current = states[state];

  button.classList.toggle("is-success", state === "success");
  button.classList.toggle("is-error", state === "error");
  button.setAttribute("aria-label", current.label);
  button.title = current.label;
  button.innerHTML = `${current.icon}<span class="visually-hidden" aria-live="polite">${current.label}</span>`;
};

const fallbackCopyText = (text) => {
  const textarea = document.createElement("textarea");
  const activeElement = document.activeElement;

  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.className = "copy-textarea";
  document.body.append(textarea);
  textarea.select();
  textarea.setSelectionRange(0, textarea.value.length);

  let copied = false;
  try {
    copied = document.execCommand("copy");
  } finally {
    textarea.remove();
    if (activeElement instanceof HTMLElement) {
      activeElement.focus({ preventScroll: true });
    }
  }

  if (!copied) {
    throw new Error("Copy command was not accepted");
  }
};

const copyText = async (text) => {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return;
    } catch {
      // Fall back for browsers that expose the API but deny clipboard access.
    }
  }

  fallbackCopyText(text);
};

document.querySelectorAll(".post-body pre > code").forEach((code) => {
  const pre = code.parentElement;
  if (!pre || pre.parentElement?.classList.contains("code-block")) {
    return;
  }

  const wrapper = document.createElement("div");
  const languageLabel = document.createElement("span");
  const button = document.createElement("button");
  let resetTimer;

  wrapper.className = "code-block";
  languageLabel.className = "code-language-label";
  languageLabel.textContent = getCodeLanguage(code);
  button.className = "code-copy-button";
  button.type = "button";
  setCopyButtonState(button, "idle");

  pre.before(wrapper);
  wrapper.append(pre, languageLabel, button);

  button.addEventListener("click", async () => {
    window.clearTimeout(resetTimer);

    try {
      await copyText(code.textContent ?? "");
      setCopyButtonState(button, "success");
    } catch {
      setCopyButtonState(button, "error");
    }

    resetTimer = window.setTimeout(() => {
      setCopyButtonState(button, "idle");
    }, COPY_RESET_DELAY);
  });
});
