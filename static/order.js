function updateStatus(orderId, newStatus) {
    fetch(`/update_order_status/${orderId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            document.getElementById(`status-${orderId}`).innerText = newStatus;
            if (newStatus === "รับแล้ว") {
                // ลบแถวออกจากหน้า manage_orders
                document.getElementById(`order-${orderId}`).remove();
                
            }
        } else {
            alert("อัปเดตไม่สำเร็จ");
        }
    });
}
