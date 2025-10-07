    document.addEventListener('DOMContentLoaded', () => {
      document.querySelectorAll('.flip-btn').forEach(btn => {
        btn.addEventListener('click', e => {
          const cardInner = e.target.closest('.flip-card').querySelector('.flip-card-inner');
          cardInner.classList.toggle('flipped');
        });
      });
    });