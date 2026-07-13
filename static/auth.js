// ==========================================
// 1. SHOW / HIDE PASSWORD (Sahi Icon Toggle)
// ==========================================
const passwordInput = document.getElementById("password");
const togglePasswordSpan = document.querySelector(".toggle-password");
const eyeIcon = document.getElementById("eyeIcon");

if (passwordInput && togglePasswordSpan && eyeIcon) {
    togglePasswordSpan.addEventListener("click", function () {
        if (passwordInput.type === "password") {
            passwordInput.type = "text";
            // Jab password dikhega, toh open eye icon aayega
            eyeIcon.classList.remove("fa-eye-slash");
            eyeIcon.classList.add("fa-eye");
        } else {
            passwordInput.type = "password";
            // Jab password hide hoga, toh eye-slash icon aayega
            eyeIcon.classList.remove("fa-eye");
            eyeIcon.classList.add("fa-eye-slash");
        }
    });
}

// ==========================================
// 2. LOGIN BUTTON LOADING (Spinner Effect)
// ==========================================
const loginForm = document.querySelector("form");
const loginBtn = document.getElementById("loginBtn");
const btnText = document.getElementById("btnText");
const btnLoader = document.getElementById("btnLoader");

if (loginForm && loginBtn && btnText && btnLoader) {
    loginForm.addEventListener("submit", function () {
        // Double click ya multiple submissions rokne ke liye
        loginBtn.disabled = true;
        btnText.style.display = "none";
        btnLoader.style.display = "inline-flex"; 
        btnLoader.style.alignItems = "center";
        btnLoader.style.gap = "8px";
    });
}

// ==========================================
// 3. MOUSE CURSOR GLOW (Premium Smooth Move)
// ==========================================
const glow = document.querySelector(".cursor-glow");

if (glow) {
    document.addEventListener("mousemove", (e) => {
        // translate3d use karne se animation glitch free aur hardware-accelerated ho jata hai
        // -100px glow element ke center alignment ke liye hai (agar glow width 200px hai)
        glow.style.transform = `translate3d(${e.clientX - 100}px, ${e.clientY - 100}px, 0)`;
    });
}