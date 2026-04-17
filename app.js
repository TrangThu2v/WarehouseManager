const receipts = [
  {
    status: 'Hoàn thành',
    date: '31/12/2014',
    owner: 'Minh Quân',
    quantity: 6,
    total: 3000000,
    debt: 0,
  },
  {
    status: 'Hoàn thành',
    date: '31/12/2014',
    owner: 'Minh Quân',
    quantity: 8,
    total: 1650000,
    debt: 0,
  },
  {
    status: 'Hoàn thành',
    date: '31/12/2014',
    owner: 'Minh Quân',
    quantity: 8,
    total: 1900000,
    debt: 0,
  },
  {
    status: 'Hoàn thành',
    date: '31/12/2014',
    owner: 'Minh Quân',
    quantity: 2,
    total: 969000,
    debt: 0,
  },
  {
    status: 'Hoàn thành',
    date: '29/12/2014',
    owner: 'Minh Quân',
    quantity: 6,
    total: 3000000,
    debt: 0,
    highlighted: true,
  },
];

const formatMoney = (value) =>
  new Intl.NumberFormat('vi-VN', {
    maximumFractionDigits: 0,
  }).format(value);

const rows = document.getElementById('receiptRows');

rows.innerHTML = receipts
  .map(
    (item) => `
      <tr class="${item.highlighted ? 'highlight' : ''}">
        <td><span class="status">${item.status}</span></td>
        <td>${item.date}</td>
        <td>${item.owner}</td>
        <td>${item.quantity}</td>
        <td class="money">${formatMoney(item.total)}</td>
        <td>${item.debt}</td>
        <td class="delete">🗑</td>
      </tr>
    `,
  )
  .join('');
