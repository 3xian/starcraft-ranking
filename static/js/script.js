var global = {};
global.init = function() {
	$(".tips-sw").tipsy({ gravity: "sw" });
}

var newThing = {
	imageIDs: []
};
newThing.init = function() {
	if ($("#newThing").length == 0) {
		return false;
	}
	Dropzone.options.newThingDropzone = {
		init: function() {
			this.on("success", function(file, msg) {
				if ($.trim(msg).length > 0) {
					newThing.imageIDs.push(msg);
					console.log("image upload success: " + msg);
				}
			});
		}
	};
	$("#newThingDesc").cleditor({
		controls:
		"style bold italic underline strikethrough | color highlight removeformat | " +
		"link unlink image | bullets numbering indent outdent | undo redo"
	});
	$("#newThingSubmit").click(function() {
		newThing.submit();
	});
};
newThing.submit = function() {
	var newThingTitle = $.trim($("newThingTitle").text());
	if (newThingTitle.length == 0) {
		alert("产品名称还没填呢");
		return false;
	}
	var newThingSubtitle = $.trim($("newThingSubtitle").text());
	var newThingBuylink = $.trim($("newThingBuylink").text());
};

$(function() {
	global.init();
	newThing.init();
});
