import torch
import torch.nn.functional as F

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

import copy
from functions import plotsigs

#because plots broke the kernel
import os
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"

mc = pd.read_csv(r'Q:\AUH-HAEM-FORSK-MutSigDLBCL222\article_1\generated_data\DLBCL1001_trainset1_80p.csv', sep=',', index_col=0).transpose()

context = mc.columns
mutation = [s[2:5] for s in context]

x_train = mc.sample(frac=0.8)
x_test = mc.drop(x_train.index)

x_train_tensor = torch.tensor(x_train.values, 
                              dtype = torch.float32)
x_test_tensor = torch.tensor(x_test.values, 
                             dtype = torch.float32)

trainloader = torch.utils.data.DataLoader(x_train_tensor, 
                                          batch_size=8, 
                                          shuffle=True)
testloader = torch.utils.data.DataLoader(x_test_tensor, 
                                         batch_size=8)

# Creating linear (NMF autoencoder)
# 96 ==> 8 ==> 96
class AAUtoSig(torch.nn.Module):
    def __init__(self, dim1, dim2):
        super().__init__()

        
        # Building an linear encoder
        # 96 => dim1 => dim2
        self.enc1 = torch.nn.Linear(96, dim1, bias = False)
        self.enc2 = torch.nn.Linear(dim1, dim2, bias = False)
          
        # Building an linear decoder 
        # dim ==> 96
        self.dec1 = torch.nn.Linear(dim2, 96, bias = False)
            

    def forward(self, x):
        x = F.softplus(self.enc1(x))
        x = F.softplus(self.enc2(x))
        x = F.softplus(self.dec1(x))
        return x
    
# Model Initialization
n_sigs = 5
model = AAUtoSig(dim1 = 30, dim2 = n_sigs)

# Validation using MSE Loss function
loss_function = torch.nn.MSELoss(reduction='mean')
#loss_function = torch.nn.KLDivLoss()

def kl_poisson(p, q):
    return torch.mean( torch.where(p != 0, p * torch.log(p / q) - p + q, 0))


# Using an Adam Optimizer with lr = 0.1
optimizer = torch.optim.Adam(model.parameters(),
                             lr = 1e-3,
                             weight_decay = 1e-8)


#Train
epochs = 500
outputs = []

training_plot=[]
validation_plot=[]

last_score=np.inf
max_es_rounds = 50
es_rounds = max_es_rounds
best_epoch= 0
#l1_lambda = 0.001

for epoch in range(epochs):
    model.train()
    
    for data in trainloader:
      # Output of Autoencoder
      reconstructed = model(data.view(-1,96))
        
      # Calculating the loss function
      loss = loss_function(reconstructed, data.view(-1,96))
      # l1_norm = sum(p.abs().sum()
      #            for p in model.parameters())
 
      # loss = loss + l1_lambda * l1_norm
      
      # The gradients are set to zero,
      # the the gradient is computed and stored.
      # .step() performs parameter update
      optimizer.zero_grad()
      loss.backward()
      optimizer.step()
      #W = model.dec1.weight.data
    # print statistics
    with torch.no_grad():
        for p in model.parameters():
            p.clamp_(min = 0)
            
        model.eval()
        
        inputs = x_train_tensor[:]
        outputs = model(inputs)
        
        train_loss = loss_function(outputs, inputs)
        #train_loss = kl_poisson(inputs, outputs)

        training_plot.append(train_loss)
    
 

        inputs  = x_test_tensor[:]
        outputs = model(inputs)
        valid_loss = loss_function(outputs, inputs)
        #valid_loss = kl_poisson(inputs, outputs)

        
        validation_plot.append(valid_loss)
        print("Epoch {}, training loss {}, validation loss {}".format(epoch, 
                                                                      np.round(training_plot[-1],2), 
                                                                      np.round(validation_plot[-1],2)))

 #Patient early stopping - thanks to Elixir  
    if last_score > valid_loss:
        last_score = valid_loss
        best_epoch = epoch
        es_rounds = max_es_rounds
        best_model = copy.deepcopy(model)
        '''
    else:
        if es_rounds > 0:
            es_rounds -=1
        else:
            print('EARLY-STOPPING !')
            print('Best epoch found: nº {}'.format(best_epoch))
            print('Exiting. . .')
            break
'''
plt.figure(figsize=(16,12))
plt.subplot(3, 1, 1)
plt.title('Score per epoch')
plt.ylabel('Mean Squared Error')
plt.plot(list(range(len(training_plot))), validation_plot, label='Validation MSE')
plt.plot(list(range(len(training_plot))), training_plot, label='Train MSE')
plt.legend()


W = best_model.dec1.weight.data    
W_array = W.numpy()


#for i in range(n_sigs):
#    plotsigs(context, mutation, W_array[:,i])    


validation_set = pd.read_csv(r'Q:\AUH-HAEM-FORSK-MutSigDLBCL222\article_1\generated_data\DLBCL1001_testset1_20p.csv', sep=',', index_col=0).transpose()

x_validation_tensor = torch.tensor(validation_set.values, 
                             dtype = torch.float32)
res = model(x_validation_tensor)
print(loss_function(res,x_validation_tensor))