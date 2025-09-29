async function updateStatus(orderId, status) {
    try {
        const res = await fetch(`/update_order_status/${orderId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });

        const data = await res.json(); // อ่าน JSON response
        if (data.success) {
            document.getElementById(`status-${orderId}`).innerText = status;
            if (status === "รับแล้ว") {
                document.getElementById(`order-${orderId}`).remove();
            }
        } else {
            alert("เกิดข้อผิดพลาด: " + data.error);
        }
    } catch (err) {
        console.error(err);
        alert("เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์");
    }
}
