document.addEventListener("DOMContentLoaded", () => {
    const cards = document.querySelectorAll(".card");
    cards.forEach(card => {
        card.addEventListener("click", () => {
            const inner = card.querySelector(".card-inner");
            inner.classList.toggle("flipped");
        });
    });
});