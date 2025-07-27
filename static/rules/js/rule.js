let controller = function() {
    let objs = {
        matchType: document.getElementById('match-type'),
        newCheckValue: document.getElementById('new-check-value'),
        createNewRule: document.getElementById('add-check'),
        category: document.getElementById('category')
    };

    let getSetId = function() {
        let path = window.location.pathname.split('/');
        return parseInt(path[path.length - 1]);
    }

    let inits = function() {
        objs.matchType.addEventListener('change', function() {
            let selectedMatchType = this.options[this.selectedIndex];
            let valueType = selectedMatchType.getAttribute('data-value-type');
            if (valueType === 'numeric') {
                objs.newCheckValue.type = 'number';
            } else {
                objs.newCheckValue.type = 'text';
            }
        });

        objs.createNewRule.addEventListener('click', function() {
            let numberValue = null;
            let stringValue = null;
            if (objs.newCheckValue.type === 'number') {
                numberValue = parseFloat(objs.newCheckValue.value);
            } else {
                stringValue = objs.newCheckValue.value;
            }
            let rule = new Rule(
                getSetId(),
                stringValue,
                numberValue,
                objs.matchType.value,
            );
            rule.create();
        });

        objs.category.addEventListener('change', function() {
            let rule_set = new RuleSet({id: getSetId()});
            rule_set.update_category(this.value);
        });
    }();
}();