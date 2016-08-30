

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
  margin-bottom: 2px;
}

.ui-button.interaction-btn {
margin-bottom: 10px;
}

body {
  font-family: "Open Sans", sans;
}

p {
color: #1e1e1e;
}

.interaction-btn.ui-state-default {
background: rgba(51,51,51,0.2);
color: #333333;
}

.interaction-btn.ui-state-hover {
border-color: #227fb6;
background: rgba(51,51,51,0.6);
color: white;
}

    </style>
    
  </head>
  
<body>
  
  <div style="position: absolute; left: 0; right: 0; top: 0; bottom: 0; min-width: 900px; min-height: 600px;">
    
    <!-- side title -->
    <div style="background: #333333; position: absolute; left: 0; width: 50px; top: 0; bottom: 0;">
      <svg height="600px" width="50px" viewBox="0 0 50 600">
	<text transform="rotate(-90 25,10)" x="25" y="10" dy="0.35em" fill="white" text-anchor="end" font-size="30px">INTERACTIVE SVG EDITOR</text>
      </svg>
    </div>

    <!-- SVG display -->
    <p style="margin: 10px; position: absolute; left: 50px; top: 0;"><b>SVG:</b> <button>Load</button></p>
    <div id="svg" style="margin: 10px; position: absolute; left: 50px; top: 50px; bottom: 50%; right: 30%;">
      {{!code_svg}}
    </div>

    <!-- Interaction script -->
    <div style="margin: 10px; position: absolute; left: 50px; top: 50%; bottom: 60px; right: 30%;">
      <p style="margin-top: 0;"><b>INTERACTION SCRIPT:</b> <button>Load</button></p>
      <textarea id="instructions" style="width: 100%; padding: 5px; border: 1px solid #dddddd; height: 90%;" >{{initial_instr}}</textarea>
    </div>

    
    <!-- Identifiers list -->
    <div style="margin: 10px; position: absolute; left: 70%; top: 0; right: 10px; bottom: 60px; overflow-y: auto;">
      <p style="margin-top: 0;"><b>ELEMENT IDENTIFIERS:</b></p>
      <ul style="list-style: none; margin-left: 0; padding-left: 0;">
	{{!code_ids}}
      </ul>
    </div>

    <!-- Buttons -->
    <div style="margin: 10px; position: absolute; left: 50px; height: 30px; bottom: 0; right: 10px;">
      <button id="button-test" class="interaction-btn" style="width: 100%; height: 30px; max-width: 200px; ">Test</button>
      <button id="button-export" class="interaction-btn" style="width: 100%; height: 30px; max-width: 200px; ">Export HTML</button>
      <button id="button-help" class="interaction-btn" style="width: 100%; height: 30px; max-width: 200px; ">Help</button>
      <a id="export-download" style="display:none;"></a>
    </div>
    
  </div>


  
  <script>

// checkout: http://stackoverflow.com/questions/13688814/uploading-a-file-with-a-single-button

  
var ids = {{!ids}};

$("#svg svg").attr("x",0).attr("y",0).attr("width","100%").attr("height","100%");

$("#button-test").button();
$("#button-export").button();
$("#button-help").button();

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
$("#button-export").click(exportInteractive);

function testInteractive () {
    var w = window.open("about:blank", "compiled_svg");
    var formData = new FormData();
    formData.append("svg",$("#svg").html());
    formData.append("instr",$("#instructions").val());
    formData.append("ox","{{original_x}}");
    formData.append("oy","{{original_y}}");
    formData.append("ow","{{original_width}}");
    formData.append("oh","{{original_height}}");
    formData.append("frame","true");
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
				
function exportInteractive () {
    var formData = new FormData();
    formData.append("svg",$("#svg").html());
    formData.append("instr",$("#instructions").val());
    formData.append("ox","{{original_x}}");
    formData.append("oy","{{original_y}}");
    formData.append("ow","{{original_width}}");
    formData.append("oh","{{original_height}}");
    formData.append("frame","false");
    var xhr = new XMLHttpRequest();
    xhr.open("POST","/compile_svg");
    xhr.onload = function () { 
	if (xhr.status === 200) {

	    var filename = "export.html";
	    var text = [xhr.responseText];

	    var textFile = new Blob(text,{type: "text/html;charset=utf-8"});
	    var url = window.URL.createObjectURL(textFile);
	
	    /// $("body").append("<a id='download_document' href='{}' download='{}'></a>".format(url,filename))

	    var a = document.getElementById("export-download");
	    a.href = url;
	    a.download = filename;
	    
	    a.click();

	    /* delayed seems to be needed on firefox */
	    setTimeout(function(){
		window.URL.revokeObjectURL(url);  
	    }, 1000);
	} else {
	    alert("Problem with server");
	}
    }
    xhr.send(formData);
}
				
   </script>

  </body>

</html>
