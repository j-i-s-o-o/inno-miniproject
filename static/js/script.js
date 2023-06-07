const modal = document.getElementById("modal");
const openModalBtn = document.getElementById("open-modal");
const closeModalBtn = document.getElementById("close-modal");

// 모달창 열기
openModalBtn.addEventListener("click", () => {
  modal.style.zIndex = 3;
  modal.style.opacity = 1;
  //   document.body.style.overflow = "hidden"; // 스크롤바 제거
});

// 모달창 닫기
closeModalBtn.addEventListener("click", () => {
  modal.style.zIndex = -1;
  modal.style.opacity = 0;
  //   document.body.style.overflow = "auto"; // 스크롤바 보이기
});
