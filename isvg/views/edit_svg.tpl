

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

    <!-- <link rel="stylesheet" href="/static/style.css" /> -->

    <style>

/* #svg { border: 1px solid #dddddd; } */

.ui-button-text {
  font-size: 9pt;
}

.ui-button {
  margin-bottom: 2px;
}

body {
  font-family: "Open Sans", sans-serif;
}

p {
    color: #1e1e1e;
}

.interaction-btn.ui-state-default {
    background: #cccccc;
    color: #333333;
}

.interaction-btn.ui-state-hover {
    border-color: #888888;
    background: #666666;
    color: white;
}

/* change color of .interaction-btn when "selected" (border gets blue...) */

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
    <p style="margin: 10px; position: absolute; left: 50px; top: 0;"><b>SVG:</b> <input id="svg_file"  type="file" style="margin-left: 10px;"> <!--<button id="button-load-svg">Load</button></p>-->
    <div id="svg" style="margin: 10px; position: absolute; left: 50px; top: 50px; bottom: 50%; right: 30%;">
      {{!code_svg}}
    </div>

    <!-- Interaction script -->
    <div style="margin: 10px; position: absolute; left: 50px; top: 50%; bottom: 60px; right: 30%;">
      <p style="margin-top: 0;"><b>INTERACTION SCRIPT:</b> <!-- <button>Load</button></p>-->
      <textarea id="instructions" style="width: 100%; padding: 5px; border: 1px solid #dddddd; height: 90%;" >{{initial_instr}}</textarea>
    </div>
    
    <!-- Identifiers list -->
    <div style="margin: 10px; position: absolute; left: 70%; top: 0; right: 10px; bottom: 60px; overflow-y: auto;">
      <p style="margin-top: 0;"><b>ELEMENT IDENTIFIERS:</b></p>
      <ul id="identifiers_list" style="list-style: none; margin-left: 0; padding-left: 0;">
      </ul>
    </div>

    <!-- Buttons -->
    <div style="position: absolute; left: 50px; height: 50px; bottom: 0; right: 0; background: #333333;">
      <button id="button-help" class="interaction-btn" style="margin: 10px; width: 100%; height: 30px; max-width: 200px; float: right;">Help</button>
      <button id="button-export" class="interaction-btn" style="margin: 10px; width: 100%; height: 30px; max-width: 200px; float: right;">Export HTML</button>
      <button id="button-test" class="interaction-btn" style="margin: 10px; width: 100%; height: 30px; max-width: 200px; float: right;">Test</button>
      <button id="button-fonts" class="interaction-btn" style="margin: 10px; width: 100%; height: 30px; max-width: 200px; float: right;">Sans-Serif Fonts</button>
      <a id="export-download" style="display:none;"></a>
    </div>
    
  </div>

  <script>


$(run)

var GLOBAL = {
    original_x:0,
    original_y:0, 
    original_width:0, 
    original_height:0
};

var original_svg_data = {{!svg_data}}


function enableSVGButtons () { 
    $("#button-test").button("enable");
    $("#button-export").button("enable");
    
    if (GLOBAL.fonts.length !== 1 || 
	GLOBAL.fonts[0] !== "sans-serif") {
	$("#button-fonts").button("enable");
    } else {
	$("#button-fonts").button("disable");
    }
}


function run () { 
    
    $("#svg svg").attr("x",0).attr("y",0).attr("width","100%").attr("height","100%");
    
    $("#button-test").button().button("disable");
    $("#button-fonts").button().button("disable");
    $("#button-export").button().button("disable");
    $("#button-help").button().button("disable");
    
    $("#button-test").click(testInteractive);
    $("#button-export").click(exportInteractive);

    $("#button-fonts").click(changeFontsToSansSerif);

    // $("#button-load-svg").button();

    /* For some reason, $("#svg").length doesn't work. Work around: */
//    if ("{{!code_svg}}"!=="") {

    if (document.getElementById("svg").children.length > 0) {
	setupSVG(original_svg_data);
    }
    
    $("#svg_file").on("change",uploadSVG);
}

function changeFontsToSansSerif () {
    
    // Create a formdata object and add the files
    var data = new FormData();

    var svg_code = $("#svg").html();
    var blob = new Blob([svg_code], { type: "text/xml"});

    data.append("file",blob);
    
    //console.log(files[0]);
    //console.log(data);
    
    $.ajax({
	url: "/fix_fonts_svg",
	type: "POST",
	data: data,
	cache: false,
	contentType: false, // "multipart/form-data",  -- do not specify, otherwise JQ doesn't send boundary string
	dataType: "json",
	processData: false, // Don't process the files
	success: function(data, textStatus, jqXHR)
	{
	    console.log("RESULT = ",data);
	    $("#svg").html(data.svg);

	    if (data.instr!=="") {
		$("#instructions").val(data.instr);
	    }

	    setupSVG(data);
	},
	error: function(jqXHR, textStatus, errorThrown)
	{
	    // Handle errors here
	    console.log('ERRORS: ' + textStatus);
	    // STOP LOADING SPINNER
	}
    });
}


function uploadSVG () {
    var files = $("#svg_file").prop("files");
    
    /* CHECK THAT FILES IS NOT EMPTY! */

    if (files.length===0) {
	return;
    }
    
    // START A LOADING SPINNER HERE
    
    // Create a formdata object and add the files
    var data = new FormData();
    data.append("file",files[0]);
    
    //console.log(files[0]);
    //console.log(data);
    
    $.ajax({
	url: "/upload_svg",
	type: "POST",
	data: data,
	cache: false,
	contentType: false, // "multipart/form-data",  -- do not specify, otherwise JQ doesn't send boundary string
	dataType: "json",
	processData: false, // Don't process the files
	success: function(data, textStatus, jqXHR)
	{
	    console.log("RESULT = ",data);
	    $("#svg").html(data.svg);

	    if (data.instr!=="") {
		$("#instructions").val(data.instr);
	    }

	    setupSVG(data);
	},
	error: function(jqXHR, textStatus, errorThrown)
	{
	    // Handle errors here
	    console.log('ERRORS: ' + textStatus);
	    // STOP LOADING SPINNER
	}
    });
}


function setupSVG (data) {

    GLOBAL.original_x = data.original_x;
    GLOBAL.original_y = data.original_y;
    GLOBAL.original_width = data.original_width;
    GLOBAL.original_height = data.original_height;
    GLOBAL.fonts = data.fonts;
    
    $("#identifiers_list").html(data.ids_list);
    
    var ids=data.ids;
    
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

    enableSVGButtons();
}


    
function testInteractive () {
    var w = window.open("about:blank", "compiled_svg");
    var formData = new FormData();
    formData.append("svg",$("#svg").html());
    formData.append("instr",$("#instructions").val());
    formData.append("ox",GLOBAL.original_x);
    formData.append("oy",GLOBAL.original_y);
    formData.append("ow",GLOBAL.original_width);
    formData.append("oh",GLOBAL.original_height);
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
    formData.append("ox",GLOBAL.original_x);
    formData.append("oy",GLOBAL.original_y);
    formData.append("ow",GLOBAL.original_width);
    formData.append("oh",GLOBAL.original_height);
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
