from app.utils.rut_auth import rut_username, rut_default_password, clean_rut

def test_username_from_dotted():
    assert rut_username("12.345.678-9") == "12345678-9"

def test_default_password_from_plain():
    assert rut_default_password("12345678-9") == "12.345.678-9"

def test_dv_k_preserved():
    assert rut_username("9.876.543-K") == "9876543-K"
    assert rut_default_password("9876543-k") == "9.876.543-K"