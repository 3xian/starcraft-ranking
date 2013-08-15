var global = {};
global.init = function() {
	$(".tips-sw").tipsy({ gravity: "sw" });
}
global.parseTags = function(str) {
	var result = [];
	str = str.replace(/，/g, ",");
	$.each(str.split(","), function() {
		if ($.trim(this)) {
			result.push($.trim(this));
		}
	});
	return result;
}

var newThing = {
	imageIDs: [],
	editor: null
};
newThing.init = function() {
	if ($("#newThing").length == 0) {
		return false;
	}
	$("#newThingDesc").cleditor({
		controls:
		"style bold italic underline strikethrough | color highlight removeformat | " +
		"link unlink image | bullets numbering indent outdent | undo redo"
	});
	this.editor = $(".cleditorMain iframe").contents().find('body');
	Dropzone.options.newThingDropzone = {
		init: function() {
			this.on("success", function(file, msg) {
				if ($.trim(msg).length > 0) {
					newThing.imageIDs.push(msg);
					console.log("image upload success:", msg);
				}
			});
		}
	};
	$("#newThingSubmit").click(function() {
		newThing.submit();
	});
};
newThing.submit = function() {
	var newThingTitle = $.trim($("#newThingTitle").val());
	if (newThingTitle.length == 0) {
		alert("产品名称还没填呢");
		return false;
	}
	var newThingSubtitle = $.trim($("#newThingSubtitle").val());
	var newThingBuylink = $.trim($("#newThingBuylink").val());
	var newThingTags = global.parseTags($("#newThingTags").val());
	var newThingDesc = this.editor.html();

	$.post("/things/new", {
		title: newThingTitle,
		subtitle: newThingSubtitle,
		buylink: newThingBuylink,
		tags: newThingTags.toString(),
		image_ids: newThing.imageIDs.toString(),
		desc: newThingDesc
	}, function(msg) {
		var response = JSON.parse(msg);
		if (response.error) {
			alert("发布失败");
		} else {
			alert("发布成功");
			window.location = "/things/detail/" + response.thing_id;
		}
	});
};

$(function() {
	global.init();
	newThing.init();
});
