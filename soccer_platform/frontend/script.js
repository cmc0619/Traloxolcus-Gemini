function toggleSidebar() {
    document.querySelector('.sidebar').classList.toggle('open');
    document.body.classList.toggle('sidebar-open');
}

// Close sidebar when clicking outside on mobile
document.addEventListener('click', function (event) {
    const sidebar = document.querySelector('.sidebar');
    const toggle = document.querySelector('.mobile-nav-toggle');

    if (document.body.classList.contains('sidebar-open') &&
        !sidebar.contains(event.target) &&
        !toggle.contains(event.target)) {
        toggleSidebar();
    }
});
