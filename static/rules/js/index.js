let controller = function() {
    let objs = {
        createRuleSet: document.getElementById('new-rule'),
        newRuleSetName: document.getElementById('rule-set-name'),
        newRuleSetCategory: document.getElementById('default-category-name'),
    };
    let inits = function() {
        objs.createRuleSet.addEventListener('click', function() {
            let ruleSet = new RuleSet({
                name: objs.newRuleSetName.value,
                category_id: objs.newRuleSetCategory.value,
            });
            ruleSet.create();
        })
    }();
}();