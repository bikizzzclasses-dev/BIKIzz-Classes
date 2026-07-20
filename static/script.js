// ================= OPEN / REFRESH POSITION =================
if ("scrollRestoration" in history) {
    history.scrollRestoration = "manual";
}

function resetPageToTop() {
    if (window.location.hash) {
        history.replaceState(null, "", window.location.pathname + window.location.search);
    }

    window.scrollTo(0, 0);

    requestAnimationFrame(function () {
        window.scrollTo(0, 0);
    });

    setTimeout(function () {
        window.scrollTo(0, 0);
    }, 50);

    setTimeout(function () {
        window.scrollTo(0, 0);
    }, 250);
}

resetPageToTop();

window.addEventListener("pageshow", resetPageToTop);

window.addEventListener("beforeunload", function () {
    window.scrollTo(0, 0);
});

// ================= LOADER =================
window.addEventListener("load", function () {

    resetPageToTop();

    setTimeout(function () {

        const loader = document.getElementById("loader");

        if (loader) {
            loader.classList.add("loader-hide");
        }

    }, 1500);

});

// ================= MOBILE MENU =================
const menu = document.getElementById("menu-toggle");
const nav = document.getElementById("navbar-menu");

if (menu && nav) {

    menu.addEventListener("click", function () {

        nav.classList.toggle("active");

        const icon = menu.querySelector("i");

        if (icon) {

            if (nav.classList.contains("active")) {

                icon.classList.remove("fa-bars");
                icon.classList.add("fa-times");

            } else {

                icon.classList.remove("fa-times");
                icon.classList.add("fa-bars");

            }

        }

    });

}

// ================= FAQ =================
document.querySelectorAll(".faq-question").forEach(question => {

    question.addEventListener("click", function () {

        const faq = this.parentElement;

        document.querySelectorAll(".faq-box").forEach(box => {

            if (box !== faq) {
                box.classList.remove("active");
            }

        });

        faq.classList.toggle("active");

    });

});

// ================= SCROLL TO TOP =================
const topBtn = document.getElementById("topBtn");

window.addEventListener("scroll", function () {

    if (!topBtn) return;

    if (window.scrollY > 300) {

        topBtn.style.setProperty("display", "flex", "important");

    } else {

        topBtn.style.setProperty("display", "none", "important");

    }

});

if (topBtn) {

    topBtn.addEventListener("click", function () {

        window.scrollTo({

            top: 0,
            behavior: "smooth"

        });

    });

}

// ================= ACTIVE NAVBAR =================

const sections = document.querySelectorAll("section");
const navLinks = document.querySelectorAll("nav a");

window.addEventListener("scroll", () => {

    let current = "";

    sections.forEach(section => {

        const sectionTop = section.offsetTop - 120;
        const sectionHeight = section.clientHeight;

        if (pageYOffset >= sectionTop) {
            current = section.getAttribute("id");
        }

    });

navLinks.forEach(link => {

        link.classList.remove("active");

        if (link.getAttribute("href") == "#" + current) {
            link.classList.add("active");
        }

    });

});

// ================= SCROLL 3D UP REVEAL =================
const revealItems = document.querySelectorAll(
    ".course-card, .why-box, .faculty-card, .step, .faq-box, .video-box, .footer-col"
);

if ("IntersectionObserver" in window) {
    revealItems.forEach(item => item.classList.add("scroll-3d"));

    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add("is-visible");
                revealObserver.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.16,
        rootMargin: "0px 0px -60px 0px"
    });

    revealItems.forEach(item => revealObserver.observe(item));
} else {
    revealItems.forEach(item => item.classList.add("is-visible"));
}
