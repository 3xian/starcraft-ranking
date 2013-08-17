var global = {};
global.init = function() {
	$(".tips-sw").tipsy({ gravity: "sw" });
};
global.parseTags = function(str) {
	var result = [];
	str = str.replace(/，/g, ",");
	$.each(str.split(","), function() {
		if ($.trim(this)) {
			result.push($.trim(this));
		}
	});
	return result;
};

var things = {};
things.init = function() {
	if ($('.kuke-cascade').length == 0) {
		return false;
	}
	$('.kuke-cascade').imagesLoaded(function() {
		var handler = null;

		// Prepare layout options.
		var options = {
			itemWidth: 220, // Optional, the width of a grid item
			autoResize: true, // This will auto-update the layout when the browser window is resized.
			container: $('#cascade'),
			offset: 15, // Optional, the distance between grid items
			flexibleWidth: 320 // Optional, the width of a grid item
		};

		function applyLayout() {
			$('.kuke-cascade').imagesLoaded(function() {
				// Destroy the old handler
				if (handler.wookmarkInstance) {
					handler.wookmarkInstance.clear();
				}

				// Create a new layout handler.
				handler = $('.kuke-cascade li');
				handler.wookmark(options);
			});
		}

		function onScroll(event) {
			// Check if we're within 100 pixels of the bottom edge of the broser window.
			var winHeight = window.innerHeight ? window.innerHeight : $(window).height(); // iphone fix
			var closeToBottom = ($(window).scrollTop() + winHeight > $(document).height() - 100);

			if (closeToBottom) {
				var items = $('.kuke-cascade li');
				var firstTen = items.slice(0, 10);
				$('.kuke-cascade').append(firstTen.clone());

				applyLayout();
			}
		};
		$(window).bind('scroll', onScroll);

		handler = $('.kuke-cascade li');
		handler.wookmark(options);
	});
};

var newThing = {
	imageIDs: [],
	editor: null
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
					console.log("image upload success:", msg);
				} else {
					console.log("image upload error");
				}
			});
		}
	};

	$("#newThingDesc").cleditor({
		controls:
		"style bold italic underline strikethrough | color highlight removeformat | " +
		"link unlink image | bullets numbering indent outdent | undo redo"
	});
	this.editor = $(".cleditorMain iframe").contents().find('body');

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
	var newThingSubtitle = $("#newThingSubtitle").val();
	var newThingBuylink = $("#newThingBuylink").val();
	var newThingTags = global.parseTags($("#newThingTags").val());
	var newThingPrice = $("#newThingPrice").val();
	var newThingDesc = this.editor.html();

	$.post("/things/new", {
		title: newThingTitle,
		subtitle: newThingSubtitle,
		buylink: newThingBuylink,
		tags: newThingTags.toString(),
		price: newThingPrice,
		image_ids: newThing.imageIDs.toString(),
		desc: newThingDesc
	}, function(msg) {
		var response = JSON.parse(msg);
		if (response.error) {
			alert("发布失败");
		} else {
			alert("发布成功，请耐心等待管理员审核");
			window.location = "/things/detail/" + response.thing_id;
		}
	});
};

$(function() {
	global.init();
	things.init();
	newThing.init();
});
