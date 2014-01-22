$(function() {
	$('#submitContest').click(function() {
      $.post('/sc/contest/add', {
        winners: $('#winners').val(),
        losers: $('#losers').val()
      }, function(msg) {
		if (msg == 'ok') {
			window.location.reload();
		} else {
			alert(msg);
		}
      });
	});
});
