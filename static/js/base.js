document.addEventListener("DOMContentLoaded", function () {
    const html = document.documentElement;
    const themeToggle = document.getElementById("theme-toggle");
    const appConfig = document.getElementById("app-config");

    const notificationBellLink = document.getElementById("notification-bell-link");
    const notificationBell = document.getElementById("notification-bell");
    const notificationBadge = document.getElementById("notification-badge");
    const sidebarNotificationBadge = document.getElementById("sidebar-notification-badge");

    const floatingChatIcon = document.getElementById("floating-chat-icon");
    const sidebarChatIcon = document.getElementById("sidebar-chat-icon");
    const dashboardGreeting = document.getElementById("dashboard-greeting");

    const savedTheme = localStorage.getItem("hms-theme");

    if (savedTheme) {
        html.setAttribute("data-theme", savedTheme);
    }

    if (themeToggle) {
        themeToggle.addEventListener("click", function () {
            const currentTheme = html.getAttribute("data-theme") || "light";
            const nextTheme = currentTheme === "light" ? "dark" : "light";
            html.setAttribute("data-theme", nextTheme);
            localStorage.setItem("hms-theme", nextTheme);
        });
    }

    if (!appConfig) {
        return;
    }

    const notificationsUrl = appConfig.dataset.notificationsUrl || "";
    const chatUnreadUrl = appConfig.dataset.chatUnreadUrl || "";
    const workflowSoundUrl = appConfig.dataset.workflowSoundUrl || "";
    const chatSoundUrl = appConfig.dataset.chatSoundUrl || "";
    const isAuthenticated = appConfig.dataset.isAuthenticated === "true";
    const isDashboardPage = appConfig.dataset.isDashboardPage === "true";
    const dashboardIdentityLabel = appConfig.dataset.dashboardIdentityLabel || "";
    const dashboardWelcomeUntil = appConfig.dataset.dashboardWelcomeUntil || "";

    let lastUnreadNotificationCount = parseInt(appConfig.dataset.unreadNotificationsCount || "0", 10);
    let lastUnreadChatCount = parseInt(appConfig.dataset.unreadChatCount || "0", 10);

    let audioUnlocked = false;
    let workflowAudio = null;
    let chatAudio = null;

    function createAudio(url) {
        if (!url) return null;
        const audio = new Audio(url);
        audio.preload = "auto";
        return audio;
    }

    workflowAudio = createAudio(workflowSoundUrl);
    chatAudio = createAudio(chatSoundUrl);

    function unlockAudio() {
        audioUnlocked = true;

        const unlockList = [workflowAudio, chatAudio].filter(Boolean);
        unlockList.forEach(function (audio) {
            try {
                audio.volume = 1;
                const playPromise = audio.play();
                if (playPromise && typeof playPromise.then === "function") {
                    playPromise
                        .then(function () {
                            audio.pause();
                            audio.currentTime = 0;
                        })
                        .catch(function () {
                            // silent
                        });
                }
            } catch (error) {
                console.error("Audio unlock failed:", error);
            }
        });

        document.removeEventListener("click", unlockAudio);
        document.removeEventListener("touchstart", unlockAudio);
        document.removeEventListener("keydown", unlockAudio);
    }

    document.addEventListener("click", unlockAudio, { once: true });
    document.addEventListener("touchstart", unlockAudio, { once: true });
    document.addEventListener("keydown", unlockAudio, { once: true });

    function playNotificationSound(audio) {
        if (!audio || !audioUnlocked) return;

        try {
            audio.pause();
            audio.currentTime = 0;
            const playPromise = audio.play();
            if (playPromise && typeof playPromise.catch === "function") {
                playPromise.catch(function () {
                    // silent
                });
            }
        } catch (error) {
            console.error("Notification sound failed:", error);
        }
    }

    function showWorkflowBellButton(unreadCount) {
        if (!notificationBellLink) return;

        if (unreadCount > 0) {
            notificationBellLink.classList.remove("hidden");
            notificationBellLink.classList.add("btn", "btn-sm", "btn-outline", "text-white", "border-white", "hover:bg-blue-700", "relative");
        } else {
            notificationBellLink.classList.add("hidden");
        }
    }

    function updateNotificationBadgeElement(element, unreadCount) {
        if (!element) return;

        if (unreadCount > 0) {
            element.textContent = unreadCount;
            element.classList.remove("hidden");
            element.classList.add("animate-pulse");
        } else {
            element.textContent = "0";
            element.classList.add("hidden");
            element.classList.remove("animate-pulse");
        }
    }

    function updateNotificationUI(unreadCount) {
        showWorkflowBellButton(unreadCount);
        updateNotificationBadgeElement(notificationBadge, unreadCount);
        updateNotificationBadgeElement(sidebarNotificationBadge, unreadCount);

        if (notificationBell && unreadCount > lastUnreadNotificationCount) {
            notificationBell.classList.remove("bell-shake");
            void notificationBell.offsetWidth;
            notificationBell.classList.add("bell-shake");
            playNotificationSound(workflowAudio);
        }

        lastUnreadNotificationCount = unreadCount;
    }

    function restartMailAnimation(element) {
        if (!element) return;
        element.classList.remove("mail-bounce-loop");
        void element.offsetWidth;
        element.classList.add("mail-bounce-loop");
    }

    function setChatIconState(element, hasUnread) {
        if (!element) return;

        element.textContent = hasUnread ? "💌" : "✉️";

        if (hasUnread) {
            if (!element.classList.contains("mail-bounce-loop")) {
                element.classList.add("mail-bounce-loop");
            }
        } else {
            element.classList.remove("mail-bounce-loop");
        }
    }

    function updateChatUI(unreadChatCount) {
        const hasUnread = unreadChatCount > 0;

        setChatIconState(floatingChatIcon, hasUnread);
        setChatIconState(sidebarChatIcon, hasUnread);

        if (unreadChatCount > lastUnreadChatCount) {
            restartMailAnimation(floatingChatIcon);
            restartMailAnimation(sidebarChatIcon);
            playNotificationSound(chatAudio);
        }

        lastUnreadChatCount = unreadChatCount;
    }

    function updateDashboardGreeting() {
        if (!dashboardGreeting || !isDashboardPage) {
            return;
        }

        if (!dashboardWelcomeUntil) {
            dashboardGreeting.textContent = dashboardIdentityLabel;
            return;
        }

        const welcomeUntilDate = new Date(dashboardWelcomeUntil);
        const now = new Date();

        if (!isNaN(welcomeUntilDate.getTime()) && now < welcomeUntilDate) {
            dashboardGreeting.textContent = `Welcome ${dashboardIdentityLabel}`;
        } else {
            dashboardGreeting.textContent = dashboardIdentityLabel;
        }
    }

    async function pollNotifications() {
        if (!notificationsUrl) return;

        try {
            const response = await fetch(notificationsUrl, {
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                },
                cache: "no-store"
            });

            if (!response.ok) return;

            const data = await response.json();
            updateNotificationUI(data.unread_count || 0);
        } catch (error) {
            console.error("Notification polling error:", error);
        }
    }

    async function pollChatUnread() {
        if (!chatUnreadUrl) return;

        try {
            const response = await fetch(chatUnreadUrl, {
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                },
                cache: "no-store"
            });

            if (!response.ok) return;

            const data = await response.json();
            updateChatUI(data.unread_chat_count || 0);
        } catch (error) {
            console.error("Chat polling error:", error);
        }
    }

    updateDashboardGreeting();
    updateNotificationUI(lastUnreadNotificationCount);
    updateChatUI(lastUnreadChatCount);

    if (isAuthenticated) {
        pollNotifications();
        pollChatUnread();

        setInterval(pollNotifications, 5000);
        setInterval(pollChatUnread, 3000);
        setInterval(updateDashboardGreeting, 30000);
    }
});