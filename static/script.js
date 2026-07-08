// ================= LOADER =================
window.addEventListener("load", function () {

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

        topBtn.style.display = "flex";

    } else {

        topBtn.style.display = "none";

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