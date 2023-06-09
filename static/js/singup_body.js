const id_text = document.getElementById("userid");
const pw_text = document.getElementById("userpw");
const nick_text = document.getElementById("usernick");
const pw_access = document.querySelectorAll("#userpwaccess > li");

/* iD Check */
id_text.addEventListener("focus", (e) => {
  document.getElementById("useridaccess").innerHTML = "";
});
id_text.addEventListener("blur", (e) => {
  let c = e.target.value.length;

  const regex = /^[a-z0-9]+$/;
  if (!regex.test(e.target.value)) {
    document.getElementById("useridaccess").innerHTML = "* 영소문자, 숫자로만 가능합니다";
    return;
  }
  if (c > 4)
    outfocus_id();
  else
    document.getElementById("useridaccess").innerHTML = "* 5글자 이상 입력해주세요";
});
var getTextLength = function (str) {
  var len = 0;
  for (var i = 0; i < str.length; i++) {
    if (escape(str.charAt(i)).length == 6) {
      len++;
    }
    len++;
  }
  return len;
}
/* Nick Check */
nick_text.addEventListener("focus", (e) => {
  document.getElementById("usernickaccess").innerHTML = "";
});
nick_text.addEventListener("blur", (e) => {
  let c = getTextLength(e.target.value);

  const regex = /^[a-zA-Zㄱ-ㅎㅏ-ㅣ가-힣0-9]+$/;
  if (!regex.test(e.target.value)) {
    document.getElementById("usernickaccess").innerHTML = "* 글자 및 숫자만 가능합니다";
    return;
  }
  if (c > 4)
    outfocus_nick();
  else
    document.getElementById("usernickaccess").innerHTML = "* 5글자 이상 입력해주세요";
});

/* PW Check */
pw_text.addEventListener("input", (e) => {
  let c = e.target.value.length;
  let d = e.target.value;
  const pw_access = document.querySelectorAll("#userpwaccess > li");

  const regex = /^[a-z0-9]+$/;
  if (!regex.test(d) || "" == d) {
    pw_access[0].innerHTML = "X lower a";
  }
  else {
    pw_access[0].innerHTML = "V lower a";
  }
  if (c >= 8 && c <= 12) {
    pw_access[1].innerHTML = "V 8 - 12 char";
  }
  else {
    pw_access[1].innerHTML = "X 8 - 12 char";
  }
})

id_text.focus();