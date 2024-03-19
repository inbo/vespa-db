export function getCookie(name) {
    console.log("getCookie")
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        console.log("document.cookie")
        const cookies = document.cookie.split(';');
        console.log(cookies)
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}