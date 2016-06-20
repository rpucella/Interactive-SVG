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

    <style>

/* #svg { border: 1px solid #dddddd; } */

.ui-button-text {
  font-size: 9pt;
}

.ui-button {
  margin-top: 1px;
  margin-bottom: 1px;
}

body {
  font-family: "Open Sans", sans;
}

    </style>

  </head>

  <body>

    <div style="position: absolute; left: 0; right: 0; top: 0; bottom: 0; min-width: 900px; min-height: 600px;">

      <p style="margin: 10px; position: absolute; left: 20px; top: 20px;"><b>SVG:</b></p>

      <div id="svg" style="margin: 10px; position: absolute; left: 20px; top: 20px; bottom: 50%; right: 40%;">
  	  {{!code_svg}}
      </div>


      <div style="margin: 10px; margin-left: 50px; position: absolute; left: 60%; top: 20px; right: 20px; bottom: 20px; overflow-y: auto;">
	<p style="margin-top: 0;"><b>ELEMENT IDENTIFIERS:</b></p>
	<ul style="list-style: none; margin-left: 0; padding-left: 0;">
	  {{!code_ids}}
	</ul>
      </div>

      <div style="margin: 10px; position: absolute; left: 20px; top: 50%; bottom: 20px; right: 40%;">
	<p style="margin-top: 0;"><b>INTERACTION SCRIPT:</b></p>
	<textarea id="instructions" style="width: 100%; padding: 5px; border: 1px solid #dddddd; height: 80%;" ></textarea>
	<span><button id="button-test" style="width: 200px; margin-right: 20px;">Test</button><button id="button-export" style="width: 200px;">Export</button></span>
      </div>

    </div>
      
  <script>
  
var ids = {{!ids}};

$("#svg svg").attr("x",0).attr("y",0).attr("width","100%").attr("height","100%");

$("#button-test").button();
$("#button-export").button();

for (var i=0; i<ids.length; i++) {
    (function(id) {
        $("#checkbox_"+id).button();
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
