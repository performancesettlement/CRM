function initialize_modal_contents() {
  $('.selectpicker').selectpicker('render');

  tinyMCE.remove('.tinymce');
  $('.tinymce').each(
    function() {
      initTinyMCE($(this));
    }
  );
  return false;
}

$(
  function() {
    $('#fm-modal').on(
      'fm.ready',
      initialize_modal_contents
    );
  }
);

/*
The selectpicker controls need to be initialized every time the FM modal
dialog loads.  This can be mostly solved with a handler for the `fm.ready`
event, but the first time the FM modal dialog loads, this script has not yet
registered the event handler.  Therefore, the initialization function needs
to be executed manually for the first initialization.
*/
initialize_modal_contents();
