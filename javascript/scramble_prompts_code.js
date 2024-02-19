function m9_scramble_prompts_tolower(str) {
  if (typeof str === "string")
    return str.toLowerCase();
  return "";
}

function m9_scramble_prompts_find_child(ele, tag, cls=null, text=null) {
  tag = m9_scramble_prompts_tolower(tag);
  // console.log ("Parent: "+String(ele));
  for (let i = 0; i < ele.childNodes.length; i++) {
    // console.log(String(i)+": "+String(ele.childNodes[i])+" > "+m9_scramble_prompts_tolower(ele.childNodes[i].tagName));
    // console.log(String(i)+": "+String(ele.childNodes[i])+" # "+String(ele.childNodes[i].classList));
    cit = ele.childNodes[i].innerText
    if (m9_scramble_prompts_tolower(ele.childNodes[i].tagName)==tag
          && (cls === null || ele.childNodes[i].classList.contains(cls))
          && (text === null || ((typeof cit)=='string' && cit.includes(text))))
      return ele.childNodes[i];
  }
  return null;
}

m9_scramble_prompts_accordion_element = null;
m9_scramble_prompts_accordion_tag = null;
m9_scramble_prompts_check_element = null;

function m9_scramble_prompts_update_enabled(event) {
  // console.log("checked: " + String(m9_scramble_prompts_check_element.checked))
  if (m9_scramble_prompts_check_element!=null) {
    if (m9_scramble_prompts_check_element.checked)
      m9_scramble_prompts_accordion_tag.classList.add("enabled");
    else
      m9_scramble_prompts_accordion_tag.classList.remove("enabled");
  }
}

function m9_scramble_prompts_loaded() {
  // alert ('loaded')
  let m9_scramble_prompts_accordion = document.getElementById("m9-tweak-weights-accordion")
  let m9_scramble_prompts_enabled = document.getElementById("m9-tweak-weights-enabled")

  if (m9_scramble_prompts_accordion==null || m9_scramble_prompts_enabled==null)
    setTimeout(() => { m9_scramble_prompts_loaded() }, 500);
  else
  {
    // console.log("got both")
    m9_scramble_prompts_accordion_element = m9_scramble_prompts_find_child(m9_scramble_prompts_accordion, "div", "label-wrap");
    if (m9_scramble_prompts_accordion_element!=null) {
      span = m9_scramble_prompts_find_child(m9_scramble_prompts_accordion_element, "span", null, "M9");
      // console.log("span: "+String(span))
      if (span!=null) {
        m9_scramble_prompts_accordion_tag = document.createElement("div");
        m9_scramble_prompts_accordion_tag.className = 'm9-tweak-weights-tag';
        m9_scramble_prompts_accordion_tag.innerText = 'enabled';
        span.appendChild(m9_scramble_prompts_accordion_tag);
      }
    }
    // console.log("m9_scramble_prompts_accordion_element: "+String(m9_scramble_prompts_accordion_element));
    
    ele = m9_scramble_prompts_find_child(m9_scramble_prompts_enabled, "label");
    if (ele!=null) {
      m9_scramble_prompts_check_element = m9_scramble_prompts_find_child(ele, "input");
      if (m9_scramble_prompts_check_element!=null){
        // console.log("Found: "+String(m9_scramble_prompts_check_element)+" > "+String(m9_scramble_prompts_check_element.tagName));
        m9_scramble_prompts_check_element.addEventListener("click", m9_scramble_prompts_update_enabled);
        m9_scramble_prompts_update_enabled(null);
      }
    }
  }
}

document.addEventListener("DOMContentLoaded", function() {
  setTimeout(() => {  m9_scramble_prompts_loaded() }, 500);
});
