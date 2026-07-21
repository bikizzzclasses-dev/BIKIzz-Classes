(function () {
  let deferredInstallPrompt = null;
  const isIos = /iphone|ipad|ipod/i.test(window.navigator.userAgent);
  const isStandalone =
    window.matchMedia("(display-mode: standalone)").matches ||
    window.navigator.standalone === true;

  function showInstallMessage(message) {
    let toast = document.querySelector(".pwa-install-toast");

    if (!toast) {
      toast = document.createElement("div");
      toast.className = "pwa-install-toast";
      document.body.appendChild(toast);
    }

    toast.textContent = message;
    toast.classList.add("show");

    setTimeout(function () {
      toast.classList.remove("show");
    }, 4200);
  }

  function setupInstallButton() {
    const installButton = document.getElementById("installAppBtn");
    if (!installButton || isStandalone) return;

    if (isIos) {
      installButton.hidden = false;
    }

    installButton.addEventListener("click", async function () {
      installButton.classList.add("is-downloading");

      setTimeout(function () {
        installButton.classList.remove("is-downloading");
      }, 1200);

      if (deferredInstallPrompt) {
        deferredInstallPrompt.prompt();
        await deferredInstallPrompt.userChoice;
        deferredInstallPrompt = null;
        return;
      }

      if (isIos) {
        showInstallMessage("iPhone par Share button tap karo, phir Add to Home Screen select karo.");
      } else {
        showInstallMessage("Browser menu me Add to Home Screen / Install App option use karo.");
      }
    });
  }

  window.addEventListener("beforeinstallprompt", function (event) {
    event.preventDefault();
    deferredInstallPrompt = event;

    const installButton = document.getElementById("installAppBtn");
    if (installButton && !isStandalone) {
      installButton.hidden = false;
    }
  });

  window.addEventListener("appinstalled", function () {
    const installButton = document.getElementById("installAppBtn");
    if (installButton) {
      installButton.hidden = true;
    }
    showInstallMessage("BIKIzz Classes app installed successfully.");
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupInstallButton);
  } else {
    setupInstallButton();
  }

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(function () {
        // PWA install still works without blocking the page if registration fails.
      });
    });
  }
})();
