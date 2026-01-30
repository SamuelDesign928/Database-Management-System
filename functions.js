function confirmDelete() {
    const productNAME = prompt("Enter product name:");
    if (productNAME) {
        document.getElementById('deleteProductNAME').value = productNAME;
        return true;
    }
    return false;
}

function cancel(url){
    window.location.href = url;
}


document.addEventListener('DOMContentLoaded', () => {
    const button = document.getElementById('addcustomer');
    if (button) {
        button.addEventListener('click', () => {
            var myWindow = window.open("", "", "width=400,height=300");

            myWindow.document.write(`
                <html>
                <head>
                    <title>Add New Customer</title>
                </head>
                <body>
                    <h1>Add New Customer</h1>
                    <form id="customerForm">
                        <label for="customerNAME">Name:</label>
                        <input type="text" id="customerNAME" name="customerNAME" required><br><br>

                        <label for="customerEMAIL">Email:</label>
                        <input type="email" id="customerEMAIL" name="customerEMAIL" required><br><br>

                        <label for="customerPHONE">Phone:</label>
                        <input type="text" id="customerPHONE" name="customerPHONE" required><br><br>

                        <input type="submit" value="Submit">
                    </form>

                    <script>
                        document.getElementById('customerForm').addEventListener('submit', function(event) {
                            event.preventDefault();
                            var formData = new FormData(this);
                            fetch('/add_customer', {
                                method: 'POST',
                                body: formData,
                            })
                            .then(response => response.text())
                            .then(text => {
                                alert(text);
                                window.close();
                                if (window.opener) {
                                    window.opener.location.reload(); // Reload the parent window to update the customer list
                                }
                            })
                            .catch(error => {
                                console.error('Error:', error);
                            });
                        });
                    </script>
                </body>
                </html>
            `);
        });
    }
});
