$(function() {
	$(".tips-sw").tipsy({gravity: "sw"});
	$("#newThingDesc").cleditor({
		controls:
			"style bold italic underline strikethrough | color highlight removeformat | " +
			"link unlink image | bullets numbering indent outdent | undo redo"
	});
});
