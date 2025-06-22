let controller = function() {
    let objs = {
        "categorySelector": document.getElementById('category'),
        "tagSelector": document.getElementById('tags'),
    }

    let getTransactionId = function() {
        let path = window.location.pathname.split('/');
        return path[path.length - 1];
    }

    let updateTransaction = function() {
        let category_id = objs.categorySelector.value;
        let transaction_id = getTransactionId();
        let transaction = new Transaction(transaction_id);
        transaction.setCategory(category_id);
    }

    let updateTags = function() {
        let tag_ids = $('#tags').val().map(id => parseInt(id));
        let transaction = new Transaction(getTransactionId());
        transaction.setTags(tag_ids);
    }

    let init = function() {
        objs.categorySelector.addEventListener('change', function() {
            updateTransaction()
        });

        $('#tags').on('changed.bs.select', function(e, clickedIndex, isSelected, previousValue) {
            updateTags();
        });

        objs.tagSelector.addEventListener('change', function() {
            console.log("tag changed");
        })
    }();
}();