from app.schemas.swimmer import SwimmerBase, SwimmerCreate, SwimmerUpdate, SwimmerStatusUpdate, SwimmerOut
from app.schemas.import_ import ImportResult, UnmatchedRow, ResolveUnmatchedRequest
from app.schemas.attendance import AttendanceRecord, AttendanceBulkCreate, AttendanceOut, AttendanceSummary
from app.schemas.convocatoria import ConvocatoriaCreate, ConvocatoriaOut, ConvocatoriaMatrix, ConvocatoriaEntriesUpdate
from app.schemas.auth import UserLogin, UserRegister, Token, UserOut