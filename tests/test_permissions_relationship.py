from app.models.user import User
from app.models.document import Documento
from app.models.permission import Permissao


def test_permissions_relationship(db_session, admin_user, test_user, test_category):
    """Validate that Permissao relationships on User work as expected

    - beneficiary.permissoes should include created permission
    - concedente.permissoes_concedidas should include created permission
    """
    # Create a document owned by admin_user
    doc = Documento(
        nome='Test Doc',
        descricao='Documento de teste',
        caminho_arquivo='/tmp/test.pdf',
        nome_arquivo_original='test.pdf',
        tamanho_bytes=1024,
        tipo_mime='application/pdf',
        hash_arquivo='abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx5678yzab9012cdef3456',
        categoria_id=test_category.id,
        usuario_id=admin_user.id
    )
    db_session.session.add(doc)
    db_session.session.commit()

    # Create a permission: test_user receives permission from admin_user
    perm = Permissao(
        documento_id=doc.id,
        usuario_id=test_user.id,
        tipo_permissao='visualizar',
        concedido_por=admin_user.id
    )
    db_session.session.add(perm)
    db_session.session.commit()

    # Reload users from session to ensure relationships are fresh
    beneficiary = db_session.session.query(User).get(test_user.id)
    concedente = db_session.session.query(User).get(admin_user.id)

    # beneficiary.permissoes is a dynamic relationship
    perms_benef = beneficiary.permissoes.all()
    assert any(p.id == perm.id for p in perms_benef)

    # concedente.permissoes_concedidas should include the permission
    perms_conced = concedente.permissoes_concedidas
    # This relationship may be a list-like; convert to list if query
    if hasattr(perms_conced, 'all'):
        perms_conced_list = perms_conced.all()
    else:
        perms_conced_list = list(perms_conced)

    assert any(p.id == perm.id for p in perms_conced_list)
