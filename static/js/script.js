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
	if ($(".kuke-cascade").length == 0) {
		return false;
	}
	$(".kuke-cascade").imagesLoaded(function() {
		var handler = null;

		// Prepare layout options.
		var options = {
			itemWidth: 220, // Optional, the width of a grid item
			autoResize: true, // This will auto-update the layout when the browser window is resized.
			container: $('#cascade'),
			offset: 15, // Optional, the distance between grid items
			flexibleWidth: 300 // Optional, the width of a grid item
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

var thingsNew = {
	imageIDs: [],
	editor: null
};
thingsNew.init = function() {
	if ($("#newThing").length == 0) {
		return false;
	}

	Dropzone.options.newThingDropzone = {
		init: function() {
			this.on("success", function(file, msg) {
				if ($.trim(msg).length > 0) {
					thingsNew.imageIDs.push(msg);
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
		thingsNew.submit();
	});
};
thingsNew.submit = function() {
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

	var url = "";
	var tid = "";
	if ($("#info").attr("tid")) {
		url = "/things/update";
		tid = $("#info").attr("tid");
	} else {
		url = "/things/new";
	}

	$.post(url, {
		title: newThingTitle,
		subtitle: newThingSubtitle,
		buylink: newThingBuylink,
		tags: newThingTags.toString(),
		price: newThingPrice,
		image_ids: thingsNew.imageIDs.toString(),
		desc: newThingDesc,
		tid: tid
	}, function(msg) {
		var response = JSON.parse(msg);
		if (response.error) {
			alert("发布失败");
		} else {
			alert("发布成功，请耐心等待管理员审核");
			window.location = "/things/detail/" + response.tid;
		}
	});
};

var thingsDetail = {
	calledQrcode: false
};
thingsDetail.initCollect = function () {
	$("#actCollect").click(function() {
		$.post("/things/collect", {
			tid: $("#thingInfo").attr("tid"),
			op: 1
		}, function(msg) {
			var response = JSON.parse(msg);
			if (response.error) {
				alert("收藏失败");
			}
			window.location.reload();
		});
	});
	$("#actDiscollect").click(function() {
		$.post("/things/collect", {
			tid: $("#thingInfo").attr("tid"),
			op: 0
		}, function(msg) {
			var response = JSON.parse(msg);
			if (response.error) {
				alert("取消收藏失败");
			}
			window.location.reload();
		});
	});
};
thingsDetail.initFavor = function () {
	$("#actFavor").click(function() {
		$.post("/things/favor", {
			tid: $("#thingInfo").attr("tid"),
			op: 1
		}, function(msg) {
			var response = JSON.parse(msg);
			if (response.error) {
				alert("没赞成功");
			} else {
				$("#actFavor").addClass("hide");
				$(".kuke-detail-favornum").text(response.favor)
				$("#actDisfavor").removeClass("hide");
			}
		});
	});
	$("#actDisfavor").click(function() {
		$.post("/things/favor", {
			tid: $("#thingInfo").attr("tid"),
			op: 0
		}, function(msg) {
			var response = JSON.parse(msg);
			if (response.error) {
				alert("取消赞失败");
			} else {
				$("#actFavor").removeClass("hide");
				$(".kuke-detail-favornum").text(response.favor)
				$("#actDisfavor").addClass("hide");
			}
		});
	});
}
thingsDetail.init = function() {
	if ($("#pikame").length == 0) {
		return false;
	}
	$("#pikame").PikaChoose({
		carousel: true,
		transition: [0],
		animationSpeed: 200,
		speed: 10000
	});
	$("#actShareWechat").click(function() {
		if (!thingsDetail.calledQrcode) {
			thingsDetail.calledQrcode = true;
			var url = "/things/qrcode?tid=" + $("#thingInfo").attr("tid"); 
			var img = $("<img />").attr('src', url).load(function() {
				if (!this.complete || typeof this.naturalWidth == "undefined" || this.naturalWidth == 0) {
					console.log('broken qrcode!');
				} else {
					$("#qrcodeLoading").hide();
					$("#qrcodeLoading").parent().append(img);
				}
			});
		}
	});
	$("#actRemove").click(function() {
		if (confirm("确定删除该产品？")) {
			$.get("/things/remove", {
				tid: $("#thingInfo").attr("tid")
			}, function(msg) {
				var response = JSON.parse(msg);
				if (response.error) {
					alert("删除失败");
				}
				window.location.href = "/";
			});
		}
	});
	this.initCollect();
	this.initFavor();
};

var admin = {};
admin.init = function () {
	if ($(".kuke-admin-permit-btn").length == 0) {
		return false;
	}
	$(".kuke-admin-permit-btn").click(function() {
		if (confirm("确定审核通过该产品？")) {
			$.get("/things/permit", {
				tid: $(this).attr("tid")
			}, function(msg) {
				var response = JSON.parse(msg);
				if (response.error) {
					alert("审核失败");
				}
				window.location.reload();
			});
		}
	});
	$(".kuke-admin-remove-btn").click(function() {
		if (confirm("确定删除该产品？")) {
			$.get("/things/remove", {
				tid: $(this).attr("tid")
			}, function(msg) {
				var response = JSON.parse(msg);
				if (response.error) {
					alert("删除失败");
				}
				window.location.reload();
			});
		}
	});
};

$(function() {
	global.init();
	things.init();
	thingsDetail.init();
	thingsNew.init();
	admin.init();
});
