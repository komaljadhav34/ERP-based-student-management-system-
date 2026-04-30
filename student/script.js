const menuToggle = document.getElementById("menu-toggle");
const sidebar = document.querySelector(".sidebar");
if (menuToggle) {
  menuToggle.addEventListener("click", () => {
    sidebar.classList.toggle("active");
  });
}


// Helper: include auth header
function authHeaders(){
  const token = sessionStorage.getItem('token');
  return token ? {'Content-Type':'application/json','Authorization':'Bearer '+token} : {'Content-Type':'application/json'};
}
// Example: load notifications into container if present
document.addEventListener('DOMContentLoaded', function(){
  const notifContainer = document.getElementById('notificationsList');
  if(notifContainer){
    fetch('/api/notifications', {headers: authHeaders()})
      .then(r=>r.json())
      .then(list=>{
        notifContainer.innerHTML = list.map(n=>`<div class="notif"><h4>${n.title}</h4><p>${n.message}</p><small>${n.created_at}</small></div>`).join('');
      }).catch(()=>{});
  }
});
