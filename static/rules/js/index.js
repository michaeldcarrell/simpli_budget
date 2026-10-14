let controller = function() {
    let objs = {
        createRuleSet: document.getElementById('new-rule'),
        newRuleSetName: document.getElementById('rule-set-name'),
        newRuleSetCategory: document.getElementById('default-category-name'),
    };
    let inits = function() {
        objs.createRuleSet.addEventListener('click', function() {
            let ruleSet;
            try {
                ruleSet = new RuleSet({
                    name: objs.newRuleSetName.value.trim(),
                    category_id: objs.newRuleSetCategory.value,
                });
            } catch (e) {
                alert('Give the rule a name and pick a category.');
                return;
            }
            ruleSet.create();
        })
    }();
}();