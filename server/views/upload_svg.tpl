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
  {{!code_svg}}
  </div>

  <div>
  <ul style="list-style: none;">
     {{!code_ids}}
  </ul>
  </div>

  <script>
  
    var ids = {{!ids}};

    for (var i=0; i<ids.length; i++) {
      (function(id) {
      document.getElementById("checkbox_"+id).addEventListener("change",
         function() { 
	   if (this.checked) { 
   	     document.getElementById(id).setAttribute("display","inline");
           } else {
   	     document.getElementById(id).setAttribute("display","none");
	   }
	 });})(ids[i]);
    }   

  </script>

  </body>

</html>
