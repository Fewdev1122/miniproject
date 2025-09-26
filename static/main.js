
class HamburgerMenu {
  constructor(menuId, hamId) {
    this.menu = document.getElementById(menuId);
    this.ham = document.getElementById(hamId);
    this.init();
  }

  init() {
    this.ham.addEventListener('click', () => this.toggle());
  }

  toggle() {
    this.menu.classList.toggle('menu-active');
  }
}

// เรียกใช้
const ham = new HamburgerMenu('menu', 'ham-menu');


document.addEventListener('DOMContentLoaded', () => {
  const hamMenu = new HamburgerMenu('menu', 'bar-menu', 'ham-menu');
  // ...existing code...
});

// ...existing code...

// ======================= INIT =======================
document.addEventListener('DOMContentLoaded', () => {
  // Hamburger
  const hamMenu = new HamburgerMenu('menu', 'bar-menu', 'ham-menu');

  // ...existing code...
});

// 2. Category Filter
class CategoryFilter {
  constructor(buttonSelector, menuListId) {
    this.buttons = document.querySelectorAll(buttonSelector);
    this.menuList = document.getElementById(menuListId);
  }

  init() {
    this.buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        this.buttons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.filter(btn.getAttribute('data-target'));
      });
    });
  }

  filter(target) {
    const allMenus = this.menuList.querySelectorAll('.list-store-box');
    allMenus.forEach(menu => {
      if (target === 'all') {
        menu.style.display = 'block';
      } else {
        menu.style.display = menu.classList.contains(target) ? 'block' : 'none';
      }
    });
  }
}

// 3. Search Filter
class MenuSearch {
  constructor(inputId) {
    this.searchInput = document.getElementById(inputId);
  }

  init() {
    this.searchInput.addEventListener('input', () => this.search());
    this.searchInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        this.search();
      }
    });
  }

  search() {
    const menuName = document.querySelectorAll('.name-menu');
    const categories = document.querySelectorAll('.list-store-box');
    const keyword = this.searchInput.value.toLowerCase();

    categories.forEach(c => c.style.display = 'none');

    menuName.forEach(item => {
      const text = item.textContent.toLowerCase();
      const parentBox = item.closest('.list-store-box');
      if (text.includes(keyword)) {
        item.style.display = 'flex';
        parentBox.style.display = 'block';
      } else {
        item.style.display = 'none';
      }
    });
  }
}

// 4. Popup & Upload
class PopupManager {
  constructor(addBtnId, popupId, delBtnId, bgId, fileInputId, iconUpId, imgSucId) {
    this.addMenu = document.getElementById(addBtnId);
    this.popup = document.getElementById(popupId);
    this.del = document.getElementById(delBtnId);
    this.bg = document.getElementById(bgId);
    this.input = document.getElementById(fileInputId);
    this.iconUp = document.getElementById(iconUpId);
    this.imgSuc = document.getElementById(imgSucId);
  }

  init() {
    this.addMenu.addEventListener('click', () => this.openPopup());
    this.del.addEventListener('click', () => this.closePopup());
    this.input.addEventListener('change', () => this.previewImage());
  }

  openPopup() {
    this.popup.classList.add('add-active');
    this.bg.classList.add('add-active');
  }

  closePopup() {
    this.popup.classList.remove('add-active');
    this.bg.classList.remove('add-active');
    this.imgSuc.src = '';
    this.imgSuc.style.display = 'none';
    this.iconUp.style.display = 'flex';
  }

  previewImage() {
    const file = this.input.files[0];
    if (file) {
      const reader = new FileReader();
      this.iconUp.style.display = 'none';

      reader.onload = (e) => {
        this.imgSuc.src = e.target.result;
        this.imgSuc.style.display = 'flex';
      };

      reader.readAsDataURL(file);
    } else {
      this.imgSuc.src = '';
      this.imgSuc.style.display = 'none';
    }
  }
}

class MenuManager {
  constructor(containerSelector) {
    this.container = document.querySelector(containerSelector);
    this.init();
  }

  // ผูก event หลัก
  init() {
    document.addEventListener('click', (e) => this.handleDeleteClick(e));
  }

  // จัดการคลิกปุ่มลบ
  handleDeleteClick(e) {
    const btn = e.target.closest('.delAdmin');
    if (!btn) return;

    const id = btn.dataset.id;
    if (confirm('ยืนยันลบเมนูนี้หรือไม่?')) {
      this.deleteMenu(id, btn);
    }
  }

  async deleteMenu(id, btn) {
    try {
      const res = await fetch(`/api/menus/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Delete failed');
      const data = await res.json();

      if (data.success) {
        this.removeMenuFromDOM(btn);
      } else {
        alert('ลบไม่สำเร็จ');
      }
    } catch (err) {
      alert('ลบไม่สำเร็จ: ' + err.message);
    }
  }

  removeMenuFromDOM(btn) {
    const box = btn.closest('.list-store-box');
    if (box) box.remove();
  }
}


const buttons = document.querySelectorAll(".option-btn");

buttons.forEach(btn => {
  btn.addEventListener("click", () => {
    // เอา active ออกจากทุกปุ่ม
    buttons.forEach(b => b.classList.remove("active"));
    // ใส่ active เฉพาะปุ่มที่คลิก
    btn.classList.add("active");
  });
});


document.addEventListener('DOMContentLoaded', () => {
  new MenuManager('#menu-list');
});


document.addEventListener('DOMContentLoaded', () => {
  // Hamburger
  const hamMenu = new HamburgerMenu('menu', 'bar-menu');
  document.getElementById('bar-menu').addEventListener('click', () => hamMenu.toggle());

  // Category
  const category = new CategoryFilter('.cagatory', 'menu-list');
  category.init();

  // Search
  const search = new MenuSearch('search');
  search.init();

  // Popup
  const popupManager = new PopupManager('add_menu', 'popup', 'del-popup', 'bgblack', 'file', 'icon-up', 'img-suc');
  popupManager.init();
});

document.addEventListener("DOMContentLoaded", () => {
  const badge = document.getElementById("cart-badge");
  const cartBtn = document.getElementById("cart-btn");
  const popup = document.getElementById("cart-popup");

  let cart = JSON.parse(localStorage.getItem("cart")) || [];
  badge.textContent = cart.length;

  cartBtn.addEventListener("click", (e) => {
    e.preventDefault();
    popup.classList.toggle("hidden");
    renderCart();
  });

  function renderCart() {
    const itemsBox = document.getElementById("cart-items");
    if (!itemsBox) return;
    if (cart.length === 0) {
      itemsBox.innerHTML = "<p>ไม่มีสินค้าในตะกร้า</p>";
      return;
    }
    itemsBox.innerHTML = cart
      .map((item) => `<div>${item.name} x ${item.qty}</div>`)
      .join("");
  }
});




