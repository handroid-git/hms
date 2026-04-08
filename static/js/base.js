document.addEventListener("DOMContentLoaded", function () {
    const html = document.documentElement;
    const themeToggle = document.getElementById("theme-toggle");
    const appConfig = document.getElementById("app-config");

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
    const isAuthenticated = appConfig.dataset.isAuthenticated === "true";
    const isDashboardPage = appConfig.dataset.isDashboardPage === "true";
    const dashboardIdentityLabel = appConfig.dataset.dashboardIdentityLabel || "";
    const dashboardWelcomeUntil = appConfig.dataset.dashboardWelcomeUntil || "";

    let lastUnreadNotificationCount = parseInt(appConfig.dataset.unreadNotificationsCount || "0", 10);
    let lastUnreadChatCount = parseInt(appConfig.dataset.unreadChatCount || "0", 10);

    function updateNotificationUI(unreadCount) {
        if (notificationBadge) {
            if (unreadCount > 0) {
                notificationBadge.textContent = unreadCount;
                notificationBadge.classList.remove("hidden");
                notificationBadge.classList.add("animate-pulse");
            } else {
                notificationBadge.textContent = "0";
                notificationBadge.classList.add("hidden");
                notificationBadge.classList.remove("animate-pulse");
            }
        }

        if (sidebarNotificationBadge) {
            if (unreadCount > 0) {
                sidebarNotificationBadge.textContent = unreadCount;
                sidebarNotificationBadge.classList.remove("hidden");
                sidebarNotificationBadge.classList.add("animate-pulse");
            } else {
                sidebarNotificationBadge.textContent = "0";
                sidebarNotificationBadge.classList.add("hidden");
                sidebarNotificationBadge.classList.remove("animate-pulse");
            }
        }

        if (notificationBell && unreadCount > lastUnreadNotificationCount) {
            notificationBell.classList.remove("bell-shake");
            void notificationBell.offsetWidth;
            notificationBell.classList.add("bell-shake");
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
                }
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
                }
            });

            if (!response.ok) return;

            const data = await response.json();
            updateChatUI(data.unread_chat_count || 0);
        } catch (error) {
            console.error("Chat polling error:", error);
        }
    }

    updateDashboardGreeting();

    if (isAuthenticated) {
        setInterval(pollNotifications, 5000);
        setInterval(pollChatUnread, 3000);
        setInterval(updateDashboardGreeting, 30000);
    }
});