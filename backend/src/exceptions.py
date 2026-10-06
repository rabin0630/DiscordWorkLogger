class AppError(Exception):
    """アプリのルールに合わない時に投げる例外

    main.pyの例外ハンドラーが、status_codeと{"detail": detail}のレスポンスにする。

    Attributes:
        status_code (int): 返すHTTPのステータスコード
        detail (str): エラーコード。"name_taken"など

    Examples:

        >>> raise AppError(409, "name_taken")
    """

    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
