-- Documentation-only SQL alternative. Preferred deployment uses scripts/deploy_semantic_view.py.
USE ROLE ${PLATFORM_PREFIX}_${ENVIRONMENT}_PLATFORM_ADMIN;
USE DATABASE ${DATABASE_NAME};
USE SCHEMA SEMANTIC;

CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML(
  '${DATABASE_NAME}.SEMANTIC',
  $$
  name: CASINO_OPERATIONS
  description: Replace this minimal body with casino_semantic_model.yaml during deployment.
  tables: []
  $$,
  TRUE
);

GRANT REFERENCES, SELECT ON SEMANTIC VIEW ${DATABASE_NAME}.SEMANTIC.CASINO_OPERATIONS
  TO ROLE ${PLATFORM_PREFIX}_${ENVIRONMENT}_CORTEX_SERVICE;
