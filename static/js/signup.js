
  // 간단한 회원가입 함수입니다.
  // 아이디, 비밀번호, 닉네임을 받아 DB에 저장합니다.
  function register() {
    $.ajax({
      type: "POST",
      url: "/api/register",
      data: {
        id_give: $("#userid").val(),
        pw_give: $("#userpw").val(),
        nickname_give: $("#usernick").val(),
      },
      success: function (response) {
        if (response["result"] == "success") {
          alert("회원가입이 완료되었습니다.");
          window.location.href = "/login";
        } else {
          alert(response["result"]);
        }
      },
    });
  }
  function erazertoken() {
    window.location.href = "/login";
  }

  function outfocus_id() {
    $.ajax({
      type: "POST",
      url: "/api/id_check",
      data: {
        id_give: $("#userid").val(),
      },
      success: function (response) {
        if (response["result"] != "success") {
          document.getElementById("useridaccess").innerHTML =
            "* 사용가능한 ID입니다.";
        } else {
          document.getElementById("useridaccess").innerHTML =
            "* 사용불가능한 ID입니다.";
        }
      },
    });
  }

  function outfocus_nick() {
    $.ajax({
      type: "POST",
      url: "/api/nick_check",
      data: {
        nickname_give: $("#usernick").val(),
      },
      success: function (response) {
        if (response["result"] != "success") {
          document.getElementById("usernickaccess").innerHTML =
            "* 사용가능한 닉네임입니다.";
        } else {
          document.getElementById("usernickaccess").innerHTML =
            "* 사용불가능한 닉네임입니다.";
        }
      },
    });
  }