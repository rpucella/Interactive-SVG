<!DOCTYPE html>

  <head>
    
    <meta charset="utf-8">
    <title>{{page_title}}</title>

    <link rel="shortcut icon" href="data:image/x-icon;," type="image/x-icon">
    <link href='https://fonts.googleapis.com/css?family=Open+Sans:400,700,400italic,700italic' rel='stylesheet' type='text/css'>

    <link rel="stylesheet" href="https://code.jquery.com/ui/1.11.4/themes/smoothness/jquery-ui.css">
    <script src="https://code.jquery.com/jquery-2.2.3.min.js"   
       integrity="sha256-a23g1Nt4dtEYOj7bR+vTu7+T8VP13humZFBJNIYoEJo="   
       crossorigin="anonymous"></script>
    <script src="https://code.jquery.com/ui/1.11.4/jquery-ui.min.js"   
	    integrity="sha256-xNjb53/rY+WmG+4L6tTl9m6PpqknWZvRt0rO1SRnJzw="   
	    crossorigin="anonymous"></script>

    <link rel="stylesheet" href="/static/style.css" />

  </head>

  <body>

  <div style="float: left;">
  <ul style="list-style: none;">
     {{!code_ids}}
  </ul>
  </div>

  <div style="float: left;" id="svg">
  {{!code_svg}}
  </div>

  <div style="clear: both;">
    <textarea id="instructions" style="width: 90%; padding: 5px; border: 1px solid #cccccc;" rows="20"></textarea>
  </div>
  
  <button id="button-test">Test</button>

  <script>
  
var ids = {{!ids}};

for (var i=0; i<ids.length; i++) {
    (function(id) {
	$("#checkbox_"+id).on("change",
			      function() { 
				  if (this.checked) { 
   				      document.getElementById(id).setAttribute("display","inline");
				  } else {
   				      document.getElementById(id).setAttribute("display","none");
				  }
			      });})(ids[i])
}

$("#button-test").click(testInteractive);

function testInteractive () {
    var w = window.open("about:blank", "compiled_svg");
    var formData = new FormData();
    formData.append("svg",$("#svg").html());
    formData.append("instr",$("#instructions").val());
    formData.append("ox","{{original_x}}");
    formData.append("oy","{{original_y}}");
    formData.append("ow","{{original_width}}");
    formData.append("oh","{{original_height}}");
    var xhr = new XMLHttpRequest();
    xhr.open("POST","/compile_svg");
    xhr.onload = (function(w) { return function() { 
	if (xhr.status === 200) {
	    w.document.write(xhr.responseText);
	    w.document.close();
	} else {
	    alert("Problem with server");
	}
    }; })(w);
    xhr.send(formData);
}
				
  </script>

  </body>

</html>
