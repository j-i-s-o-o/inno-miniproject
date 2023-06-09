let checkinTime;
let checkoutTime;
let lessTime;
let Timer_flag;
let SetTime;
let userTime_arr = [];
let SubTime = 0;
let MyNick;
let MyKey = 0;

function checkin_btn() {
    if(Timer_flag)
        return;
    let checkin_time = Date.now();
    $.ajax({
        type: "POST",
        url: "/api/time/checkin",
        data: {
            CheckInTime:checkin_time
        },
        async: false,
        success: function (data) {
        }
    });
    Timer_flag = true;
    window.location.reload();
}
function checkout_btn() {
    if(!Timer_flag)
        return;
    let checkout_time = Date.now();
    $.ajax({
        type: "POST",
        url: "/api/time/checkout",
        data: {
            CheckOutTime:checkout_time
        },
        async: false,
        success: function (data) {
        }
    });
    SetTime = 0;
    Timer_flag = false;
    window.location.reload();
}

function formatTime(timetwo) {
    let timenum = timetwo;
    let hours = Math.floor(timenum / 3600);
    let minutes = Math.floor((timenum % 3600) / 60);
    let seconds = timenum % 60;
    
    return (hours < 10 ? '0' + hours : hours) + ":" + (minutes < 10 ? '0' + minutes : minutes) + ":" + (seconds < 10 ? '0' + seconds : seconds);
}

function get_lesstime() {
    $.ajax({
        type: "GET",
        url: "/api/time/lesstime",
        data: {},
        async: false,
        success: function (data) {
            lessTime = data["LessTime"];
        }
    });
}

function load_checkin_time() {
    $.ajax({
        type: "GET",
        url: "/api/time/checkin",
        data: {},
        async: false,
        success: function (data) {
            const checkinTimeString = data["CheckInTime"];
            Timer_flag = data["Flag"];

            checkinTime = new Date(+checkinTimeString); // 문자열을 숫자로 변환하여 Date 객체로 생성
            // 현재시간 -체크인시간
            const currentTime = new Date();
            const elapsedTime = currentTime - checkinTime;
            const elapsedSeconds = Math.floor(elapsedTime / 1000);
            // SetTime에 elapsedSeconds 저장// 현재시간 -체크인시간
    }});
}
function load_checkout_time() {
    $.ajax({
        type: "GET",
        url: "/api/time/checkout",
        data: {},
        async: false,
        success: function (data) {
            Timer_flag = data["Flag"];
            const checkoutTimeString = data["CheckOutTime"];
            // if(checkoutTimeString !=""){
            //   new Date(+checkoutTimeString);
            //   const checkoutTimeElement = document.querySelector(".checkout-time");
            //   checkoutTimeElement.textContent = formatTime(checkoutTime);
            // }
            // if(flag != true){
            // // 체크아웃 시간 업데이트
            // checkoutTime = new Date(+checkoutTimeString); // 문자열을 숫자로 변환하여 Date 객체로 생성
            // const checkoutTimeElement = document.querySelector(".checkout-time");
            // checkoutTimeElement.textContent = formatTime(checkoutTime);
            // // console.log("체크아웃 시간 업데이트  확인");
            // }

            checkoutTime = new Date(+checkoutTimeString); // 문자열을 숫자로 변환하여 Date 객체로 생성

            const currentTime = new Date();
            const elapsedTime = currentTime - checkinTime;
            const elapsedSeconds = Math.floor(elapsedTime / 1000);

    }});
} 

window.onload = function() {
    tid=setInterval('msg_time()',1000) //이해
};
function msg_time() {	// 1초씩 카운트
    let CountTime = ``;
    SubTime++;
    if(Timer_flag){
        SetTime++;
        // let hours = Math.floor(SetTime / 3600);
        // let minutes = Math.floor((SetTime % 3600) / 60);
        // let seconds = SetTime % 60;
        // CountTime = `${hours < 10 ? '0' + hours : hours}:${minutes < 10 ? '0' + minutes : minutes}:${seconds < 10 ? '0' + seconds : seconds}`;
        CountTime = formatTime(SetTime);
    }
    else
        CountTime  = `00:00:00`;
    document.querySelector(".study_time").innerHTML = CountTime;

    for (const key in userTime_arr) {
        if(userTime_arr[key]['Flag'])
            userTime_arr[key]['Timer'].innerHTML = formatTime(userTime_arr[key]['Time'] + SubTime);
    }
}
$(document).ready(() => {
    
    // load_checkin_time();
    // load_checkout_time();
    // get_lesstime();
    $.ajax({
        type: "GET",
        url: "/api/nick",
        async:false,
        data: {},
        success: function (response) {
            if(response['result'] == "success")
                MyNick = response['NickName'];
        }
    });
    let bodybacktic = `
        <main>
                <nav>
                    <button onclick="window.location.href='/mypage'">마이페이지</button>
                    <button>질문게시판</button>
                    <button onclick="logout()">로그아웃</button>
                </nav>`;
    let userlist = [];
    $.ajax({
        type: "GET",
        url: "/api/member",
        async:false,
        data: {},
        success: function (response) {
            if(response['result'] == "success")
                response['member_list'].forEach(element => {
                    userlist.push({
                            'ID': element['ID'],
                            'NickName': element['NickName']
                        })
                });
        }
    });
    $.ajax({
        type: "GET",
        url: "/api/time/read_timer",
        async:false,
        data: {},
        success: function (response) {
            if(response['result'] == "success")
                response['Timer'].forEach(e =>{
                    for (const key in userlist) {
                        if (userlist[key]['NickName'] == e['NickName'])
                            userlist[key]['Timer'] = e;
                    }
                })
        }
    });
    $.ajax({
        type: "GET",
        url: "/api/time/read_timer",
        async:false,
        data: {},
        success: function (response) {
            if(response['result'] == "success")
                response['Timer'].forEach(e =>{
                    for (const key in userlist) {
                        if (userlist[key]['NickName'] == e['NickName'])
                            userlist[key]['Timer'] = e;
                    }
                })
        }
    });
    for (const key in userlist) {
        if(userlist[key]['NickName'] == MyNick)
            MyKey = key;
        const curtime = (+(userlist[key]['Timer']['CheckInTime']) == 0) ? 0 : (Date.now() - +(userlist[key]['Timer']['CheckInTime']));
        const setuptime = Math.floor((+(userlist[key]['Timer']['LessTime']) + curtime) / 1000);
        userTime_arr.push({
            'Time': setuptime,
            'Flag': userlist[key]['Timer']['Flag']
        })
    }
    SetTime = userTime_arr[MyKey]['Time'];
    Timer_flag = userTime_arr[MyKey]['Flag'];
    for (const key in userlist) {
        $.ajax({
            type: "GET",
            url: `/api/userinfo?user=${userlist[key]['NickName']}`,
            async:false,
            data: {},
            success: function (response) {
                if(response['result'] == "success")
                    userlist[key]['Info_list'] = response['info_list'];
            }
        });
    }
    /* Timer fuction */
    bodybacktic += `
    <section class="time">
        <h1 class="study_time">${formatTime(SetTime)}</h1>
        <article class="timeBtns">
            <button type="button" onclick="checkin_btn()" class="mainBtn">
                <i class="fas fa-play"></i>
            </button>
            <button type="button" onclick="checkout_btn()" class="mainBtn">
                <i class="fas fa-stop"></i>
            </button>
        </article>
    </section>
    <section class="members">`;
    for (const key in userlist) {
        let Flag = userlist[key]['Timer']['Flag'] ? "공부 중" : "휴식 중";
        bodybacktic +=
        `
        <article
            class="mem"
            id="open-modal"
            data-bs-toggle="modal"
            data-bs-target="#exampleModal_${userlist[key]['ID']}"
            >
                <h2 class="mem_name">${userlist[key]['NickName']}</h2>
                <p id="timer">${formatTime(userTime_arr[key]['Time'])}</p>
            <p>${Flag}</p>
        </article>
        `;
    }
    for (const key in userlist) {
        let img_src = userlist[key]['Info_list']['Image_url'] == 'null' ? "static/img/temp_image.png" : userlist[key]['Info_list']['Image_url'];
        let TIL_src = userlist[key]['Info_list']['TIL_url'] == "" ? "javascript:alert('비공개')" : userlist[key]['Info_list']['TIL_url'];
        bodybacktic +=
        `
        <div
            class="modal fade"
            id="exampleModal_${userlist[key]['ID']}"
            tabindex="-1"
            aria-labelledby="exampleModalLabel"
            aria-hidden="true"
        >
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <button
                            type="button"
                            class="btn-close"
                            data-bs-dismiss="modal"
                            aria-label="Close"
                        ></button>
                    </div>
                    <div class="modal-body">
                        <div class="mem_img">
                            <img
                            src="${img_src}"
                            alt=""
                            />
                        </div>
                        <div class="mem_info">
                            <h2>${userlist[key]['NickName']}</h2>
                            <a href="${TIL_src}" class="mem_info-TIL">TIL 주소</a>
                            <div class="mem_info-hobbys">${userlist[key]['Info_list']['Hobby']}</div>
                            <button type="button" class="mainBtn mem_info-alert">
                            찌르기
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        `;
    }
    bodybacktic += `</main>`;

    document.querySelector("body").innerHTML = bodybacktic;

    let temp_timer = document.querySelectorAll("#timer");
    for (const key in userTime_arr) {
        userTime_arr[key]['Timer'] = temp_timer[key];
    }
})

/*
stop <i class="fas fa-stop"></i>
my timer
<section class="time">
    <h1 class="study_time">07:15:00</h1>
    <article class="timeBtns">
        <button href="#" class="mainBtn">
        <i class="fas fa-play"></i>
        </button>
        <button href="#" class="mainBtn">
        <i class="fas fa-pause"></i>
        </button>
    </article>
</section>
member card ex)
<article
    class="mem"
    id="open-modal"
    data-bs-toggle="modal"
    data-bs-target="#exampleModal_<DB_ID>"
>
    <h2 class="mem_name"><DB_NickName></h2>
    <p><DB_Timer></p>
    <p><DB_Timer_Flag></p>
</article>

<!-- Modal -->
<div
class="modal fade"
id="exampleModal_Ans"
tabindex="-2"
aria-labelledby="exampleModalLabel"
aria-hidden="true"
>
<div class="modal-dialog modal-dialog-centered">
    <div class="modal-content">
    <div class="modal-header">
        <button
        type="button"
        class="btn-close"
        data-bs-dismiss="modal"
        aria-label="Close"
        ></button>
    </div>
    <div class="modal-body">
        <div class="mem_img">
        <img
            src="static/img/temp_image.png"
            alt=""
        />
        </div>
        <div class="mem_info">
        <h2>안지수</h2>
        <a href="#" class="mem_info-TIL">TIL 주소</a>
        <div class="mem_info-hobbys">게임하기</div>
        <button type="button" class="mainBtn mem_info-alert">
            찌르기
        </button>
        </div>
    </div>
    </div>
</div>
</div>
*/