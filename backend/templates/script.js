function sendForm(form) {
  var skin_types = document.getElementsByName('skin_type');
  var skin_type = null;
  for (i = 0; i < skin_types.length; i++) {
    if (skin_types[i].checked)
      skin_type = skin_types[i];
  }
  let allergies = document.getElementById("allergies");
  console.log(skin_type);
  console.log(allergies.value);
  // pass to python function to get results
}

function displayProducts(name) {
  document.getElementById("answer-box").innerHTML = ""
  fetch("/products?" + new URLSearchParams({ product_name: name }).toString())
    .then((response) => response.json())
    .then((data) => data.forEach(row => {

      let tempDiv = document.createElement("div")
      tempDiv.innerHTML = answerBoxTemplate(row.product_name, row.product_url)
      document.getElementById("answer-box").appendChild(tempDiv)
    }));
}

function answerBoxTemplate(name, url) {
  return `<div class=''>
      <h3 class='product-name'>${name}</h3>
      <p class='product-url'>${url}</p>
  </div>`
}