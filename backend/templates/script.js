function sendForm(form) {
  var skin_types = document.getElementsByName('skin_type');
  var skin_type = null;
  for (i = 0; i < skin_types.length; i++) {
    if (skin_types[i].checked)
      skin_type = skin_types[i];
  }
  var product_types = document.getElementsByName('skin_type');
  var skin_type = null;
  for (i = 0; i < product_types.length; i++) {
    if (product_types[i].checked)
      product_type = product_types[i];
  }

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

// pass the price to the python function
const rangeInput = document.querySelectorAll(".range-input input"),
priceInput = document.querySelectorAll(".price-input input"),
range = document.querySelector(".slider .progress");
let priceGap = 1000;
priceInput.forEach(input =>{
    input.addEventListener("input", e =>{
        let minPrice = parseInt(priceInput[0].value),
        maxPrice = parseInt(priceInput[1].value);
        
        if((maxPrice - minPrice >= priceGap) && maxPrice <= rangeInput[1].max){
            if(e.target.className === "input-min"){
                rangeInput[0].value = minPrice;
                range.style.left = ((minPrice / rangeInput[0].max) * 100) + "%";
            }else{
                rangeInput[1].value = maxPrice;
                range.style.right = 100 - (maxPrice / rangeInput[1].max) * 100 + "%";
            }
        }
    });
});
rangeInput.forEach(input =>{
    input.addEventListener("input", e =>{
        let minVal = parseInt(rangeInput[0].value),
        maxVal = parseInt(rangeInput[1].value);
        if((maxVal - minVal) < priceGap){
            if(e.target.className === "range-min"){
                rangeInput[0].value = maxVal - priceGap
            }else{
                rangeInput[1].value = minVal + priceGap;
            }
        }else{
            priceInput[0].value = minVal;
            priceInput[1].value = maxVal;
            range.style.left = ((minVal / rangeInput[0].max) * 100) + "%";
            range.style.right = 100 - (maxVal / rangeInput[1].max) * 100 + "%";
        }
    });
});