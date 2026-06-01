/** @odoo-module **/

document.addEventListener('click', function (e) {
    const target = e.target;
    // Kiểm tra xem người dùng có click vào ảnh trong ma trận ảnh không
    if (target.matches('.dl_dossier_image_matrix .o_attachment .o_image_box img')) {
        e.preventDefault();
        e.stopPropagation();
        
        // Lấy đường dẫn ảnh
        const src = target.getAttribute('src');
        if (!src) return;

        // Tạo khung Overlay hiển thị toàn màn hình
        const overlay = document.createElement('div');
        overlay.id = 'dl_lightbox_overlay';
        overlay.style.position = 'fixed';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.width = '100vw';
        overlay.style.height = '100vh';
        overlay.style.backgroundColor = 'rgba(0,0,0,0.85)';
        overlay.style.zIndex = '10000';
        overlay.style.display = 'flex';
        overlay.style.justifyContent = 'center';
        overlay.style.alignItems = 'center';
        overlay.style.cursor = 'zoom-out';
        
        // Tạo thẻ ảnh phóng to
        const img = document.createElement('img');
        img.src = src;
        img.style.maxWidth = '90vw';
        img.style.maxHeight = '90vh';
        img.style.objectFit = 'contain';
        img.style.boxShadow = '0 5px 25px rgba(0,0,0,0.5)';
        img.style.borderRadius = '8px';
        img.style.transition = 'transform 0.2s';
        
        overlay.appendChild(img);
        document.body.appendChild(overlay);
        
        // Tắt khi click ra ngoài hoặc click vào ảnh
        overlay.addEventListener('click', () => {
            overlay.remove();
        });

        // Tắt khi ấn nút Esc
        document.addEventListener('keydown', function escListener(e) {
            if (e.key === 'Escape') {
                const node = document.getElementById('dl_lightbox_overlay');
                if (node) node.remove();
                document.removeEventListener('keydown', escListener);
            }
        });
    }
}, true); // Sử dụng capture phase để chặn sự kiện download mặc định của Odoo
