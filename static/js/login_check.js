function releasetoken(){
    let result;
    $.ajax({
        type: "GET",
        url: "/api/login_check",
        async: false,
        data: {},
        success: function (response) {
            if(response['result'] == "success")
                result = true;
            else
                result =  false;
        }
    });
    return result;
}