
class XCloneApiClient {
    constructor() {
        this.csrfToken =
            this.getCookie("csrftoken") ||
            document.querySelector("[name='csrfmiddlewaretoken']")?.value ||
            "";
        this.bindEvents();
    }

    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(";").shift();
        return "";
    }

    async request(url, options = {}) {
        const headers = options.headers || {};
        if (!(options.body instanceof FormData)) {
            headers["Content-Type"] = "application/json";
        }
        headers["X-CSRFToken"] = this.csrfToken;
        const response = await fetch(url, { ...options, headers });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw data;
        }
        return data;
    }

    bindEvents() {

        // Login
        const loginForm = document.getElementById("loginForm");
        if(loginForm){
            loginForm.addEventListener("submit", async (e) => {
                e.preventDefault();
                const formData = new FormData(loginForm);
                try {
                    await this.request("/api/v1/auth/login/",{
                        method: "POST",
                        body: JSON.stringify({
                            username: formData.get("username"),
                            password: formData.get("password"),
                        }),
                    });
                    window.location.assign("/");
                } catch (error) {
                    window.alert(
                        error.detail || "Não foi possível entrar. Verifique suas credenciais!"
                    );
                }
            });
        }

        // Logout
        const sair = document.getElementById("logoutBtn");
        if(sair){
            console.log("olá");
            sair.addEventListener("click", async () => {
                try {
                    await this.request("/api/v1/auth/logout/", { method: "POST" });
                    window.location.assign("/login/");
                } catch (error) {
                    console.error("Falha ao encerrar sessão:", error);
                    window.alert("Não foi possível sair. Tente novamente.");
                }
            });
        }

        // Criação de postagem
        const postForm = document.getElementById("createPostForm");
        if (postForm) {
            postForm.addEventListener("submit", async (e) => {
                e.preventDefault();
                const formData = new FormData(postForm);
                await this.request("/api/v1/posts/", { method: "POST", body: formData });
                window.location.reload();
            });
        }

        // Edição opcional de perfil
        const profileForm = document.getElementById("editProfileForm");
        if (profileForm) {
            profileForm.addEventListener("submit", async (e) => {
                e.preventDefault();
                const formData = new FormData();
                for (const [key, val] of new FormData(profileForm).entries()) {
                    if (val !== "" && (!(val instanceof File) || val.size > 0)) {
                        formData.append(key, val);
                    }
                }
                await this.request("/api/v1/users/me/", { method: "PATCH", body: formData });
                window.location.reload();
            });
        }

        // Curtidas
        document.querySelectorAll(".js-like-btn").forEach((btn) => {
            btn.addEventListener("click", async () => {
                const postId = btn.dataset.postId;
                const res = await this.request(`/api/v1/posts/${postId}/like/`, { method: "POST" });
                btn.querySelector(".js-likes-count").textContent = res.likes_count;
                btn.classList.toggle("text-danger", res.liked);
                btn.classList.toggle("text-secondary", !res.liked);
            });
        });

        // Seguir / Deixar de seguir
        document.querySelectorAll(".js-follow-btn").forEach((btn) => {
            btn.addEventListener("click", async () => {
                const username = btn.dataset.username;
                const res = await this.request(`/api/v1/users/${username}/follow/?toggle=true`, {
                    method: "POST",
                });
                btn.textContent = res.following ? "Seguindo" : "Seguir";
                window.location.reload();
            });
        });

        // Comentários
        document.querySelectorAll(".js-comment-form").forEach((form) => {
            form.addEventListener("submit", async (e) => {
                e.preventDefault();
                const postId = form.dataset.postId;
                const content = form.querySelector("input[name='content']").value;
                await this.request(`/api/v1/posts/${postId}/comments/`, {
                    method: "POST",
                    body: JSON.stringify({ content }),
                });
                window.location.reload();
            });
        });
    }
}

document.addEventListener("DOMContentLoaded", () => {
    window.xApp = new XCloneApiClient();
});
