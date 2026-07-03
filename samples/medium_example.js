/**
 * Utilidades para manejo de usuarios.
 * Módulo de complejidad media — algunas funciones bien escritas,
 * otras con lógica anidada excesiva.
 */

// Valida un email con regex básica
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Busca un usuario por id en una lista.
 * @param {Array} users
 * @param {number} id
 */
function findUserById(users, id) {
    return users.find(u => u.id === id) || null;
}

// Procesa lista de pedidos con múltiples ramas de decisión
function processOrders(orders, discount, taxRate, minFree, currency) {
    let total = 0;
    let fees = 0;
    let report = [];

    for (let i = 0; i < orders.length; i++) {
        const order = orders[i];
        if (order.status === 'pending') {
            if (order.amount > 0) {
                if (discount > 0 && order.eligible) {
                    order.amount = order.amount * (1 - discount);
                } else if (order.vip) {
                    order.amount = order.amount * 0.9;
                }
                let tax = order.amount * taxRate;
                let shipping = order.amount >= minFree ? 0 : 5.99;
                if (currency !== 'USD') {
                    if (currency === 'EUR') {
                        order.amount *= 0.92;
                        tax *= 0.92;
                        shipping *= 0.92;
                    } else if (currency === 'MXN') {
                        order.amount *= 17.5;
                        tax *= 17.5;
                        shipping *= 17.5;
                    }
                }
                total += order.amount + tax + shipping;
                fees += shipping;
                report.push({ id: order.id, final: order.amount + tax + shipping });
            }
        } else if (order.status === 'cancelled') {
            report.push({ id: order.id, final: 0, cancelled: true });
        }
    }

    return { total, fees, report };
}

module.exports = { validateEmail, findUserById, processOrders };
