#code to test some toy cases
import numpy as np 
import torch
import torch.nn as nn
from scipy.optimize import linprog
from utils import get_squared_grad_norm

z = np.array([[1, 2]], dtype=np.float32)
# z = np.array([1,2], dtype=np.float32)
theta_star = np.array([[1,2], [3,4]], dtype=np.float32)
print(z, theta_star)

theta_new = np.array([[10,2], [30,4]], dtype=np.float32)

class toy(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(toy, self).__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        model = nn.Sequential(
            nn.Linear(input_dim, output_dim, bias=False),
        )
        self.model = model

        with torch.no_grad():
            self.model[0].weight = torch.nn.Parameter(torch.from_numpy(theta_new.T).float())
            
    def forward(self, x):
        return self.model(x)


def train_model(input, target_old, model, lr):
    loss_fn = nn.MSELoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=lr)
    for i in range(100):
        
        output = model(input)
        with torch.no_grad():
            target_new = get_delta_c(output)
        loss = loss_fn(output, target_new)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        with torch.no_grad():
            print("output", output)
            solve_lp(output)
            for p in model.parameters():
                print(p)
        print(loss.item())
        # exit()
    return model

def solve_lp(c_t):
    A = np.array([1,1], dtype=np.float32()).reshape(1,2)
    b = np.array([5])

    c_t = c_t.detach().numpy()

    for j in range(1):
        sol = linprog(c = c_t, A_eq= A, b_eq = b)
        print("sol", sol.x)

    # exit()

def get_delta_c(c_t_batch):
    
    

    for i in range(1):
        c_t = c_t_batch.detach().numpy().reshape(2)

        c_new = np.zeros_like(c_t)
        delta_c = np.ones((c_t.shape[0]+1+4))
        delta_c[2] = -1
        delta_c[0] = 0
        delta_c[1] = 0

        b = -c_t[0]+c_t[1] #-1 for reduced cost if necessary

        A = np.array([1, -1, 1, 0, 0, 0, 0], dtype=np.float32).reshape(1,7)
        A_eq = np.array([[1, 0, 0, -1, 0, 1, 0], [0, 1, 0, 0, -1, 0, 1]],  dtype=np.float32).reshape(2,7)
        b_eq = np.array([0, 0], dtype=np.float32).reshape(2,1)
        # print(c_t.shape, A.shape, b.shape, delta_c.shape, c_t, delta_c)
        bounds = [(0, None) for i in range (7)]

        for j in range(2):
            bounds[j]= (-c_t[j], None)

        x = linprog(c = delta_c, A_ub=A, b_ub=b, A_eq= A_eq, b_eq = b_eq, bounds=bounds)

       
        with torch.no_grad():
            c_new = c_t + x.x[:2]
        
        print("res", x.x[:3], c_t)
        
    print(c_t_batch, c_new)
    # exit()
    
    return torch.from_numpy(c_new).float()

def get_lr_by_armijo_with_target(model, input, target, prev_lr):
        with torch.no_grad():
            loss_fn = nn.MSELoss()
            z = input
            func, params = make_functional(model)
            grad_norm = get_squared_grad_norm(model.parameters())

            base_lr = prev_lr
            base_loss = loss_fn(target, func(params, z))

            lr = base_lr
            while True:
                for p1, p2 in zip(self.model.parameters(), params):
                    p2.data = p1.data - lr*p1.grad
                
                loss = loss_fn(target, func(params, z))
                if loss <= base_loss - 0.5*lr*grad_norm:
                    break
                if lr < 1e-10:
                    break
                lr *= 0.9
                # print("intermediate loss", loss,"lr", lr, "base_loss", base_loss, "grad_norm", grad_norm)
            return lr
    

input = torch.from_numpy(z).float().reshape(-1,2)
target = torch.from_numpy(z @ theta_star).float()
print(target)
model = toy(2,2)
# print(model(input))
# exit()
model = train_model(input, target, model, 0.1)
